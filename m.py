import cv2
import streamlit as st
from tempfile import NamedTemporaryFile
import os
import pyaudio
import wave
import threading
from moviepy.editor import VideoFileClip, AudioFileClip


def record_audio(audio_duration, filename):
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 44100

    p = pyaudio.PyAudio()

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []

    st.write(f"Recording audio for {audio_duration} seconds...")

    for _ in range(0, int(fs / chunk * audio_duration)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()


def record_video(capture_duration):
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    temp_file = NamedTemporaryFile(delete=False, suffix='.avi')
    out = cv2.VideoWriter(temp_file.name, fourcc, 20.0, (640, 480))

    st.write(f"Recording video for {capture_duration} minutes...")

    display = st.empty()  # Create an empty placeholder

    start_time = cv2.getTickCount()
    while int((cv2.getTickCount() - start_time) / cv2.getTickFrequency() * 1000) < capture_duration * 60 * 1000:
        ret, frame = cap.read()

        if ret:
            out.write(frame)
            display.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="BGR",
                          use_column_width=True)  # Update the image

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()
    out.release()

    return temp_file.name


def merge_video_audio(video_file, audio_file, output_file):
    video_clip = VideoFileClip(video_file)
    audio_clip = AudioFileClip(audio_file)

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file, codec='libx264')

    video_clip.close()
    audio_clip.close()


if __name__ == "__main__":
    st.title('Are you ready to shake your legs??')

    capture_duration = st.slider('Select recording duration (minutes)', 0.5, 4.0, 2.0, 0.5)
    audio_duration = capture_duration * 60

    if st.button('Start Recording'):
        if capture_duration < 0.5:
            st.error("Minimum video recording duration should be 30 seconds (0.5 minutes).")
        else:
            video_file_path = record_video(capture_duration)

            audio_thread = threading.Thread(target=record_audio, args=(audio_duration, 'recorded_audio.wav'))
            audio_thread.start()

            st.write('Recording completed!')

            audio_thread.join()

            st.write('Merging video and audio...')
            merged_file_path = 'merged_video_audio.mp4'
            merge_video_audio(video_file_path, 'recorded_audio.wav', merged_file_path)

            with open(merged_file_path, 'rb') as f:
                st.download_button('Download Merged Video', f.read(), 'merged_video_audio.mp4')

            os.remove(video_file_path)
            os.remove('recorded_audio.wav')
            os.remove(merged_file_path)
