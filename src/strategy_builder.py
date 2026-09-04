import os
from .config import BlobMap, BLOBS_DIR, LISTS_DIR, ZAPRET_DIR

blob_map = BlobMap()


def _resolve_list(name):
    mapping = {
        "general": "domains-general.txt",
        "general-user": "domains-general-user.txt",
        "google": "domains-google.txt",
        "exclude": "domains-exclude.txt",
        "exclude-user": "domains-exclude-user.txt",
    }
    fname = mapping.get(name, name)
    p = LISTS_DIR / fname
    return str(p) if p.exists() else str(LISTS_DIR / fname)


def _resolve_ipset(name):
    mapping = {
        "all": "ipset-all.txt",
        "exclude": "ipset-exclude.txt",
        "exclude-user": "ipset-exclude-user.txt",
    }
    fname = mapping.get(name, name)
    p = LISTS_DIR / fname
    return str(p) if p.exists() else str(LISTS_DIR / fname)


def _blob_fullfile(name):
    name = str(name)
    if name.startswith("0x"):
        return None
    fname = blob_map.resolve(name)
    p = BLOBS_DIR / fname
    return str(p) if p.exists() else None


def _collect_blob_names(sections):
    names = set()
    for sec in sections:
        for de in sec.get("desync", []):
            if not isinstance(de, dict):
                continue
            v = de.get("blob")
            if v:
                names.add(v)
            for key in ("blob_fakes", "blob_fakes_tls", "blob_fakes_unknown"):
                val = de.get(key)
                if isinstance(val, list):
                    names.update(val)
                elif val:
                    names.add(val)
            val = de.get("blob_fakes_http")
            if isinstance(val, list):
                names.update(val)
            elif val:
                names.add(val)
            for key in ("seqovl_pattern", "pattern"):
                val = de.get(key)
                if val and not str(val).startswith("0x"):
                    names.add(val)
    return names


def _build_filter_args(filt, settings):
    args = []

    if "tcp" in filt:
        ports = str(filt["tcp"])
        if "GameFilterTCP" in ports:
            ports = settings.game_filter_tcp
        if ports:
            args.append(f"--filter-tcp={ports}")

    if "udp" in filt:
        ports = str(filt["udp"])
        if "GameFilterUDP" in ports:
            ports = settings.game_filter_udp
        if ports:
            args.append(f"--filter-udp={ports}")

    if "l3" in filt:
        args.append(f"--filter-l3={filt['l3']}")

    if "l7" in filt:
        l7 = filt["l7"]
        if isinstance(l7, list):
            l7 = ",".join(l7)
        args.append(f"--filter-l7={l7}")

    if "l7_filter" in filt:
        args.append(f"--filter-l7={filt['l7_filter']}")

    if "hostlist" in filt:
        for h in filt["hostlist"]:
            args.append(f"--hostlist={_resolve_list(h)}")

    if "hostlist_domains" in filt:
        domains = ",".join(filt["hostlist_domains"])
        args.append(f"--hostlist-domains={domains}")

    if "hostlist_exclude" in filt:
        for h in filt["hostlist_exclude"]:
            args.append(f"--hostlist-exclude={_resolve_list(h)}")

    if "hostlist_exclude_domains" in filt:
        domains = ",".join(filt["hostlist_exclude_domains"])
        args.append(f"--hostlist-exclude-domains={domains}")

    if "ipset" in filt:
        args.append(f"--ipset={_resolve_ipset(filt['ipset'])}")

    if "ipset_exclude" in filt:
        for ie in filt["ipset_exclude"]:
            args.append(f"--ipset-exclude={_resolve_ipset(ie)}")

    return args


def _add_fooling_params(params, d):
    fooling = d.get("fooling")
    tcp_seq = d.get("tcp_seq")

    if fooling:
        if isinstance(fooling, str):
            parts = [f.strip() for f in fooling.split(",")]
        else:
            parts = [fooling]

        for f in parts:
            if f == "ts":
                params.append("tcp_ts=-1")
            elif f == "badseq":
                if tcp_seq is not None:
                    params.append(f"tcp_seq={tcp_seq}")
                else:
                    params.append("tcp_seq=-2")
            elif f == "md5sig":
                params.append("tcp_md5")
    elif tcp_seq is not None:
        params.append(f"tcp_seq={tcp_seq}")

    if d.get("tcp_md5"):
        params.append("tcp_md5")


def _add_common_params(params, d, extra):
    if "repeats" in d:
        params.append(f"repeats={d['repeats']}")

    if "any_protocol" in d and d["any_protocol"]:
        params.append("any_protocol=1")

    if "cutoff" in d:
        cutoff = d["cutoff"]
        if isinstance(cutoff, str) and cutoff.startswith("n"):
            n = _n_str_to_packets(cutoff)
            params.append(f"out_range=-d{n}")
        elif isinstance(cutoff, str) and cutoff.startswith("d"):
            params.append(f"out_range=-{cutoff}")

    if extra:
        params.extend(extra)

    _add_fooling_params(params, d)


def _build_one_desync(d, extra):
    func = d["func"]
    params = []

    _add_common_params(params, d, extra)

    if "blob" in d:
        params.append(f"blob={d['blob']}")

    if "pos" in d:
        params.append(f"pos={d['pos']}")

    if "seqovl" in d:
        params.append(f"seqovl={d['seqovl']}")

    if "seqovl_pattern" in d:
        params.append(f"seqovl_pattern={d['seqovl_pattern']}")

    if "pattern" in d:
        params.append(f"pattern={d['pattern']}")

    if "host" in d:
        mod = f"host={d['host']}"
        if d.get("altorder"):
            mod += ",altorder=1"
        params.append(f"mod={mod}")

    if "tls_mod" in d:
        params.append(f"tls_mod={d['tls_mod']}")

    if "dir" in d:
        params.append(f"dir={d['dir']}")

    param_str = ":".join(params)
    if param_str:
        return f"--lua-desync={func}:{param_str}"
    else:
        return f"--lua-desync={func}"


def _build_desync_args(desync_list, extra):
    args = []
    for d in desync_list:
        func = d["func"]

        has_blob_fakes = "blob_fakes" in d or "blob_fakes_tls" in d or "blob_fakes_http" in d or "blob_fakes_unknown" in d

        if func == "fake" and has_blob_fakes:
            blob_lists = []
            if "blob_fakes" in d:
                for b in d["blob_fakes"]:
                    blob_lists.append(("blob", b))
            if "blob_fakes_tls" in d:
                for b in d["blob_fakes_tls"]:
                    blob_lists.append(("blob", b))
            if "blob_fakes_http" in d:
                blob_lists.append(("blob_fakes_http", d["blob_fakes_http"]))
            if "blob_fakes_unknown" in d:
                unknown = d["blob_fakes_unknown"]
                if isinstance(unknown, list):
                    for b in unknown:
                        blob_lists.append(("blob", b))
                else:
                    blob_lists.append(("blob", unknown))

            base_params = []
            _add_common_params(base_params, d, extra)

            for key, blob_name in blob_lists:
                entry = dict(d)
                entry["blob"] = blob_name
                entry.pop("blob_fakes", None)
                entry.pop("blob_fakes_tls", None)
                entry.pop("blob_fakes_http", None)
                entry.pop("blob_fakes_unknown", None)

                fake_params = list(base_params)
                fake_params.append(f"blob={blob_name}")

                param_str = ":".join(fake_params)
                args.append(f"--lua-desync={func}:{param_str}")
        else:
            args.append(_build_one_desync(d, extra))

    return args


def _n_str_to_packets(n_str):
    try:
        return int(n_str[1:])
    except (ValueError, IndexError):
        return 3


def _ipid_extra(filt):
    ipid = filt.get("ip_id")
    return [f"ip_id={ipid}"] if ipid else []


def build_command(strategy_key, strategy_data, settings):
    exe = str(ZAPRET_DIR / "winws2.exe")
    lua_dir = str(ZAPRET_DIR / "lua")

    sections = strategy_data["sections"]
    cmd = [exe]

    wf_tcp = settings.wf_tcp_full()
    wf_udp = settings.wf_udp_full()
    cmd.append(f"--wf-tcp-out={wf_tcp}")
    cmd.append(f"--wf-udp-out={wf_udp}")

    cmd.append(f'--lua-init=@{os.path.join(lua_dir, "zapret-lib.lua")}')
    cmd.append(f'--lua-init=@{os.path.join(lua_dir, "zapret-antidpi.lua")}')

    for blob_name in sorted(_collect_blob_names(sections)):
        fpath = _blob_fullfile(blob_name)
        if fpath:
            cmd.append(f"--blob={blob_name}:@{fpath}")

    for part in settings.get("wf_parts", []):
        part_path = str(ZAPRET_DIR / "windivert.filter" / part)
        cmd.append(f'--wf-raw-part=@{part_path}')

    for i, section in enumerate(sections):
        if i > 0:
            cmd.append("--new")
        filt = section["filter"]
        cmd.extend(_build_filter_args(filt, settings))
        cmd.extend(_build_desync_args(section["desync"], _ipid_extra(filt)))

    return cmd


def get_all_strategies():
    data = load_yaml_strategies()
    return data.get("strategies", {})


def load_yaml_strategies():
    from .config import load_yaml, CONFIG_DIR
    return load_yaml(CONFIG_DIR / "strategies.yaml")
