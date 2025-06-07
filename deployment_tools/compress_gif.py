from PIL import Image, ImageSequence
from PIL.Image import Resampling  # Importa explicitamente o Resampling
import os
import sys


def compress_gif(input_path, output_path, max_size_mb=8, resize_factor=0.8, fps_factor=2):
    """
    Compresses a GIF to fit within the specified size limit (in MB) for Discord.
    - Resizes (scales dimensions by resize_factor).
    - Reduces frames (drops every nth frame using fps_factor).

    Args:
        input_path (str): Path to the input GIF file.
        output_path (str): Path to save the compressed GIF.
        max_size_mb (int): Maximum size of the GIF in MB.
        resize_factor (float): Factor to scale dimensions (e.g., 0.8 reduces dimensions by 20%).
        fps_factor (int): Factor to drop frames (1 keeps all, 2 keeps every second frame, etc.).

    Returns:
        bool: True if compression succeeded, False otherwise.
    """
    try:
        # Open the original GIF
        with Image.open(input_path) as gif:
            # Get original frames as a sequence
            original_frames = list(ImageSequence.Iterator(gif))
            original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            print(f"Original size: {original_size_mb:.2f} MB")

            # Scale down dimensions of each frame
            frames = []
            for frame in original_frames[::fps_factor]:  # Reduce frame count by FPS factor
                new_size = (
                    int(frame.width * resize_factor),
                    int(frame.height * resize_factor)
                )
                frames.append(frame.resize(new_size,  Resampling.LANCZOS))

            # Save compressed GIF
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=gif.info["duration"],
                loop=0,
            )

            # Check compressed size
            compressed_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"Compressed size: {compressed_size_mb:.2f} MB")

            # Recursively compress if still too large
            if compressed_size_mb > max_size_mb and resize_factor > 0.1:
                print("Compressed GIF still too large. Recursively compressing...")
                return compress_gif(output_path, output_path, max_size_mb, resize_factor * 0.9, fps_factor)

            # Successful compression
            print("Compression completed successfully!")
            return True

    except Exception as e:
        print(f"Failed to compress GIF: {e}")
        return False


if __name__ == "__main__":
    # Example usage with command line arguments
    if len(sys.argv) < 3:
        print("Usage: python compress_gif.py <input_gif_path> <output_gif_path>")
        exit()

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    MAX_SIZE_MB = 8  # Default Discord limit for free users

    success = compress_gif(input_path, output_path, max_size_mb=MAX_SIZE_MB)
    if success:
        print(f"Compressed GIF saved to: {output_path}")
    else:
        print("GIF compression failed.")