import sys

file_path = 'plugins/merger.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Threads
content = content.replace('"-threads","1"', '"-threads","2"')

# 2. Chunk Size
content = content.replace('CHUNK_SIZE   = 10', 'CHUNK_SIZE   = 5')

# 3. Phase 2 speed change
v2_phase2_orig = '''            # Chunk parts: always lossless (speed applied at final merge only)
            ok, err = await _ffmpeg_merge(
                chunk_files_sorted, part_path, None, mtype, None, 1.0, False, progress_cb=chunk_prog)'''

v2_phase2_new = '''            # Chunk parts: apply speed chunk-by-chunk to save MASSIVE amounts of RAM
            ok, err = await _ffmpeg_merge(
                chunk_files_sorted, part_path, None, mtype, None, speed, False, progress_cb=chunk_prog)'''

content = content.replace(v2_phase2_orig, v2_phase2_new)

# 4. Phase 3 speed change
v2_phase3_orig = '''        ok, err = await _ffmpeg_merge(
            part_files_sorted, out_path, metadata, mtype,
            cover, speed, make_video, effective_cover_for_video, outro_cover, cumulative_secs, progress_cb=final_prog)'''

v2_phase3_new = '''        # Speed already applied in Phase 2, so enforce 1.0x here
        ok, err = await _ffmpeg_merge(
            part_files_sorted, out_path, metadata, mtype,
            cover, 1.0, make_video, effective_cover_for_video, outro_cover, cumulative_secs, progress_cb=final_prog)'''

content = content.replace(v2_phase3_orig, v2_phase3_new)

# 5. Muxing Queue
content = content.replace('"-max_muxing_queue_size", "1024"', '"-max_muxing_queue_size", "4096"')
content = content.replace('"-max_muxing_queue_size","2048"', '"-max_muxing_queue_size","4096"')
content = content.replace('"-max_muxing_queue_size", "2048"', '"-max_muxing_queue_size", "4096"')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Optimization complete.")
