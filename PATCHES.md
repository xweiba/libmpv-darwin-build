# Downstream patches

This fork follows `Predidit/libmpv-darwin-build` and retains its pinned
FFmpeg 6.0 and mpv 0.36.0 sources.

## Nested custom media I/O

- `ffmpeg-segmented-custom-io.patch` adds a default-off `allow_custom_io`
  demuxer option for HLS and DASH. Unknown protocols are delegated only when
  the application opts in; existing HTTP, file, and protocol checks are
  unchanged.
- `mpv-nested-stream-callback.patch` lets nested FFmpeg reads use protocols
  registered through `mpv_stream_cb_add_ro`. A protocol must also appear in
  FFmpeg's `protocol_whitelist`; access-reference origin and cancellation are
  inherited from the parent stream.

Regression validation uses one immutable HLS URL for direct and callback I/O,
then checks full duration, continuous playback, seek, and cache growth. The
patches can be removed when both behaviors are available in released upstream
FFmpeg and mpv builds used by media-kit.
