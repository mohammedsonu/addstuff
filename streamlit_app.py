import streamlit as st
from PIL import Image
import tempfile
import os
import subprocess

st.title("Image + Audio to Video Converter")

num_clips = st.number_input("Number of image-audio pairs", min_value=1, max_value=10, value=2)

images = []
audios = []

for i in range(num_clips):
    st.subheader(f"Pair {i+1}")
    col1, col2 = st.columns(2)
    with col1:
        img = st.file_uploader(f"Upload Image {i+1}", type=["jpg", "jpeg", "png"], key=f"img_{i}")
        images.append(img)
    with col2:
        aud = st.file_uploader(f"Upload Audio {i+1}", type=["mp3", "wav", "m4a"], key=f"aud_{i}")
        audios.append(aud)

if st.button("Create Video"):
    if all(images) and all(audios):
        with st.spinner("Creating video..."):
            temp_dir = tempfile.mkdtemp()
            
            normalized_audios = []
            
            for i in range(num_clips):
                audio_path = os.path.join(temp_dir, f"audio_{i}_orig.mp3")
                with open(audio_path, "wb") as f:
                    f.write(audios[i].read())
                
                normalized_audio = os.path.join(temp_dir, f"audio_{i}.aac")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', audio_path,
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-ar', '48000',
                    '-ac', '2',
                    normalized_audio
                ]
                
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    st.error(f"Audio conversion error: {result.stderr}")
                    st.stop()
                
                normalized_audios.append(normalized_audio)
            
            video_parts = []
            
            for i in range(num_clips):
                img = Image.open(images[i])
                img = img.convert('RGB')
                
                width, height = img.size
                if width % 2 != 0:
                    width -= 1
                if height % 2 != 0:
                    height -= 1
                img = img.resize((width, height))
                
                img_path = os.path.join(temp_dir, f"img_{i}.png")
                img.save(img_path, quality=100)
                
                temp_video = os.path.join(temp_dir, f"video_{i}.ts")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-framerate', '1',
                    '-i', img_path,
                    '-i', normalized_audios[i],
                    '-c:v', 'libx264',
                    '-tune', 'stillimage',
                    '-c:a', 'copy',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    '-f', 'mpegts',
                    temp_video
                ]
                
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    st.error(f"FFmpeg error: {result.stderr}")
                    st.stop()
                
                video_parts.append(temp_video)
            
            if len(video_parts) == 1:
                output_path = os.path.join(temp_dir, "final_output.mp4")
                cmd = ['ffmpeg', '-y', '-i', video_parts[0], '-c', 'copy', output_path]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    st.error(f"FFmpeg error: {result.stderr}")
                    st.stop()
            else:
                concat_list = "|".join(video_parts)
                output_path = os.path.join(temp_dir, "final_output.mp4")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', f'concat:{concat_list}',
                    '-c', 'copy',
                    '-bsf:a', 'aac_adtstoasc',
                    output_path
                ]
                
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    st.error(f"FFmpeg concat error: {result.stderr}")
                    st.stop()
            
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            
            st.success("Video created successfully!")
            st.download_button(
                label="Download Video",
                data=video_bytes,
                file_name="output_video.mp4",
                mime="video/mp4"
            )
            
    else:
        st.error("Please upload all images and audio files")
