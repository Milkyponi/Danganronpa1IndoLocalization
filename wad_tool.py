import os
import sys
import struct
import time

def read_wad_metadata(fh):
    magic = fh.read(4)
    if magic != b'AGAR':
        raise RuntimeError('Not an AGAR WAD archive')
    v1, v2 = struct.unpack('<II', fh.read(8))
    extra_len = struct.unpack('<I', fh.read(4))[0]
    extra = fh.read(extra_len)
    
    file_count = struct.unpack('<I', fh.read(4))[0]
    files = []
    for _ in range(file_count):
        s_len = struct.unpack('<I', fh.read(4))[0]
        path = fh.read(s_len).decode('utf8').replace('\\', '/')
        size, offset = struct.unpack('<QQ', fh.read(16))
        files.append((path, size, offset))
        
    dir_count = struct.unpack('<I', fh.read(4))[0]
    dirs = []
    for _ in range(dir_count):
        s_len = struct.unpack('<I', fh.read(4))[0]
        dpath = fh.read(s_len).decode('utf8').replace('\\', '/')
        ecnt = struct.unpack('<I', fh.read(4))[0]
        entries = []
        for _ in range(ecnt):
            es_len = struct.unpack('<I', fh.read(4))[0]
            ename = fh.read(es_len).decode('utf8').replace('\\', '/')
            etype = struct.unpack('B', fh.read(1))[0]
            entries.append((ename, etype))
        dirs.append((dpath, entries))
    base_offset = fh.tell()
    return (v1, v2), extra, files, dirs, base_offset

def build_dirs_from_files(file_paths):
    tree = {'': {'dirs': set(), 'files': []}}
    for fp in file_paths:
        parts = fp.split('/')
        for i in range(len(parts) - 1):
            pdir = '/'.join(parts[:i])
            cdir = parts[i]
            if pdir not in tree:
                tree[pdir] = {'dirs': set(), 'files': []}
            tree[pdir]['dirs'].add(cdir)
        ldir = '/'.join(parts[:-1])
        fname = parts[-1]
        if ldir not in tree:
            tree[ldir] = {'dirs': set(), 'files': []}
        tree[ldir]['files'].append(fname)
        
    dirs_list = []
    # Hierarchical sort: root, then depth
    for dpath in sorted(tree.keys(), key=lambda x: (x.count('/'), x) if x else (-1, '')):
        entries = []
        for d in sorted(tree[dpath]['dirs']):
            entries.append((d, 1)) # 1 = directory
        for f in sorted(tree[dpath]['files']):
            entries.append((f, 0)) # 0 = file
        dirs_list.append((dpath, entries))
    return dirs_list

def patch_wad(orig_wad_path, override_dir, output_wad_path):
    t0 = time.time()
    print(f"Reading metadata from {orig_wad_path}...")
    with open(orig_wad_path, 'rb') as orig_f:
        version, extra, files, orig_dirs, base_offset = read_wad_metadata(orig_f)
        
        # Scan override directory
        override_files = {}
        for root, _, fnames in os.walk(override_dir):
            for fn in fnames:
                full_p = os.path.join(root, fn)
                rel_p = os.path.relpath(full_p, override_dir).replace('\\', '/')
                override_files[rel_p] = full_p
                
        print(f"Original files in WAD: {len(files)}, Override files provided: {len(override_files)}")
        
        # Build new file list
        new_files_metadata = []
        cur_offset = 0
        file_sources = [] # (is_override, path_or_orig_offset, size)
        
        # Map of existing files in original WAD
        orig_file_paths = set(p for p, s, o in files)
        
        for path, size, offset in files:
            if path in override_files:
                new_size = os.path.getsize(override_files[path])
                new_files_metadata.append((path, new_size, cur_offset))
                file_sources.append((True, override_files[path], new_size))
                cur_offset += new_size
            else:
                new_files_metadata.append((path, size, cur_offset))
                file_sources.append((False, offset, size))
                cur_offset += size
                
        # Also add any brand new files from override that weren't in orig
        for path, full_p in sorted(override_files.items()):
            if path not in orig_file_paths:
                new_size = os.path.getsize(full_p)
                new_files_metadata.append((path, new_size, cur_offset))
                file_sources.append((True, full_p, new_size))
                cur_offset += new_size
                print(f"Added new file: {path} ({new_size} bytes)")
                
        all_paths = [p for p, s, o in new_files_metadata]
        new_dirs = build_dirs_from_files(all_paths)
        
        print(f"Writing patched WAD to {output_wad_path}...")
        tmp_output = output_wad_path + '.tmp'
        with open(tmp_output, 'wb') as out_f:
            # 1. Header
            out_f.write(b'AGAR')
            out_f.write(struct.pack('<II', version[0], version[1]))
            out_f.write(struct.pack('<I', len(extra)))
            out_f.write(extra)
            
            # 2. Files table
            out_f.write(struct.pack('<I', len(new_files_metadata)))
            for path, size, offset in new_files_metadata:
                pb = path.encode('utf8')
                out_f.write(struct.pack('<I', len(pb)))
                out_f.write(pb)
                out_f.write(struct.pack('<QQ', size, offset))
                
            # 3. Dirs table
            out_f.write(struct.pack('<I', len(new_dirs)))
            for dpath, entries in new_dirs:
                dpb = dpath.encode('utf8')
                out_f.write(struct.pack('<I', len(dpb)))
                out_f.write(dpb)
                out_f.write(struct.pack('<I', len(entries)))
                for ename, etype in entries:
                    enb = ename.encode('utf8')
                    out_f.write(struct.pack('<I', len(enb)))
                    out_f.write(enb)
                    out_f.write(struct.pack('B', etype))
                    
            new_base_offset = out_f.tell()
            print(f"Wrote headers ({new_base_offset} bytes, {len(new_files_metadata)} files, {len(new_dirs)} dirs).")
            
            # 4. Stream data content
            chunk_size = 1024 * 1024 * 4 # 4 MB buffer
            for is_override, src, size in file_sources:
                if is_override:
                    with open(src, 'rb') as f_in:
                        while True:
                            buf = f_in.read(chunk_size)
                            if not buf: break
                            out_f.write(buf)
                else:
                    orig_f.seek(base_offset + src)
                    left = size
                    while left > 0:
                        n = min(left, chunk_size)
                        buf = orig_f.read(n)
                        out_f.write(buf)
                        left -= len(buf)

        os.replace(tmp_output, output_wad_path)
        print(f"Patched WAD finished in {time.time()-t0:.2f}s! Total size: {os.path.getsize(output_wad_path):,} bytes.")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 wad_tool.py <orig_wad> <override_dir> <output_wad>")
        sys.exit(1)
    patch_wad(sys.argv[1], sys.argv[2], sys.argv[3])
