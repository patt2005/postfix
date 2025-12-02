"""
Video Watermarking Script
Adds a logo watermark to videos with animation effects using moviepy
"""

from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import os


def add_watermark(
    video_path: str,
    output_path: str = None,
    logo_path: str = "images/logo.png",
    start_time: float = 3,
    fade_duration: float = 1.0,
    logo_scale: float = 0.15,
    position: str = "bottom_center",
    margin: int = 20
):
    """
    Add an animated watermark to a video.

    Args:
        video_path (str): Path to the input video file
        output_path (str): Path for the output video (optional, will auto-generate if None)
        logo_path (str): Path to the logo image (default: images/logo.png)
        start_time (float): Time in seconds when logo should appear (default: 3)
        fade_duration (float): Duration of fade-in animation in seconds (default: 1.0)
        logo_scale (float): Scale of logo relative to video width (default: 0.15 = 15% of video width)
        position (str): Position of logo - "bottom_center", "bottom_left", "bottom_right", etc.
        margin (int): Margin from edges in pixels (default: 20)

    Returns:
        str: Path to the output video file
    """

    # Load the video
    print(f"Loading video: {video_path}")
    video = VideoFileClip(video_path)

    # Load the logo
    print(f"Loading logo: {logo_path}")
    logo = ImageClip(logo_path)

    # Calculate logo dimensions based on video width
    logo_width = int(video.w * logo_scale)
    logo = logo.resize(width=logo_width)

    # Calculate position based on video dimensions
    if position == "bottom_center":
        x_pos = (video.w - logo.w) / 2
        y_pos = video.h - logo.h - margin
    elif position == "bottom_left":
        x_pos = margin
        y_pos = video.h - logo.h - margin
    elif position == "bottom_right":
        x_pos = video.w - logo.w - margin
        y_pos = video.h - logo.h - margin
    elif position == "top_center":
        x_pos = (video.w - logo.w) / 2
        y_pos = margin
    elif position == "top_left":
        x_pos = margin
        y_pos = margin
    elif position == "top_right":
        x_pos = video.w - logo.w - margin
        y_pos = margin
    elif position == "center":
        x_pos = (video.w - logo.w) / 2
        y_pos = (video.h - logo.h) / 2
    else:
        # Default to bottom center
        x_pos = (video.w - logo.w) / 2
        y_pos = video.h - logo.h - margin

    # Set logo position
    logo = logo.set_position((x_pos, y_pos))

    # Set logo duration (from start_time to end of video)
    logo_duration = video.duration - start_time
    logo = logo.set_duration(logo_duration)

    # Set logo to start at specified time
    logo = logo.set_start(start_time)

    # Apply fade-in animation
    print(f"Applying fade-in animation (duration: {fade_duration}s)")
    logo = logo.crossfadein(fade_duration)

    # Composite the logo onto the video
    print("Compositing logo onto video...")
    final_video = CompositeVideoClip([video, logo])

    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_watermarked.mp4"

    # Write the result
    print(f"Writing output to: {output_path}")
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        fps=video.fps
    )

    # Close clips to free memory
    video.close()
    logo.close()
    final_video.close()

    print("Watermarking complete!")
    return output_path


def add_watermark_batch(video_paths, **kwargs):
    """
    Add watermark to multiple videos.

    Args:
        video_paths (list): List of video file paths
        **kwargs: Arguments to pass to add_watermark function

    Returns:
        list: List of output video paths
    """
    output_paths = []

    for i, video_path in enumerate(video_paths, 1):
        print(f"\n{'='*60}")
        print(f"Processing video {i}/{len(video_paths)}")
        print(f"{'='*60}")

        try:
            output_path = add_watermark(video_path, **kwargs)
            output_paths.append(output_path)
        except Exception as e:
            print(f"Error processing {video_path}: {str(e)}")
            output_paths.append(None)

    return output_paths


if __name__ == "__main__":
    import sys

    video_path = "./images/video.mp4"

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    result = add_watermark(
        video_path=video_path,
        output_path=None,
        logo_path="images/logo.png",
        start_time=3,
        fade_duration=1.0,
        logo_scale=0.3,
        position="bottom_center",
        margin=250
    )

    print(f"\nSuccess! Watermarked video saved to: {result}")
