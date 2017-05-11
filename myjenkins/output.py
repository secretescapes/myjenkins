

def output_frame(frame, html=False):
    """Output the frame to console."""
    if frame.empty:
        return

    print(frame.to_html() if html else frame.to_string())
