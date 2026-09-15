# Downstream patches

## Cached Live Photo excerpts (0.6.8-mediaio.3)

The default video flavor enables only the MP4/MOV muxers and the AAC ADTS
conversion bitstream filter. This lets mpv `dump-cache` preserve the original
audio and video for finite Live Photo exports without enabling general encoders
or the GPL flavor. Photos pairing and H.264/AAC encoding remain native app work.

The iOS artifact contains device arm64 and simulator arm64/x86_64 slices.
Both CocoaPods archive and Swift Package binary checksums must be updated
together in the consuming media-kit fork. Verify an actual cache excerpt has
both audio and video before accepting a release; successful playback alone
does not verify muxer availability. Remove these downstream flags when the
upstream default video flavor provides the same finite-export capabilities.

Local Xcode 26 builds also require the libpng standard `math.h` include and
Apple's `__sincosf` declaration for HarfBuzz. The local Xcode store hash is a
machine build input, not a portable change to the CI Xcode 16.1 configuration.

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
  inherited from the parent stream. When the first `io_open` returns a custom
  top-level AVIO context, mpv explicitly sets `AVFMT_FLAG_CUSTOM_IO` and owns
  its stream, buffer, and AVIO shell; FFmpeg must not close callback opaque as
  a `URLContext`.
- `ffmpeg-segmented-io-cancel.patch` checks the demuxer interrupt callback
  before HLS/DASH opens another nested URL. The mpv bridge also checks its
  cancellation token before and after synchronous stream creation so dispose
  does not wait for every later segment timeout.

Regression validation uses one immutable HLS logical resource for direct and
callback I/O, then checks full duration, three generation-advancing seeks,
cache growth, a 10-minute continuous playback window, and bounded dispose. The
patches can be removed when both behaviors are available in released upstream
FFmpeg and mpv builds used by media-kit.
