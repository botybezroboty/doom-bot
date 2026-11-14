"""Zapis zgodnego wideo MP4 z klatek RGB."""
import imageio_ffmpeg


class Video:
    def __init__(self, path, width, height, fps=35):
        self.writer = imageio_ffmpeg.write_frames(
            str(path), (width, height), fps=fps, codec='libx264',
            pix_fmt_in='rgb24', pix_fmt_out='yuv420p', macro_block_size=1,
            output_params=['-movflags', '+faststart'],
        )
        self.writer.send(None)

    def write(self, frame):
        self.writer.send(frame.tobytes())

    def close(self):
        self.writer.close()
