// gif_decoder.h — S106 GIF-ANIM-1 (MG-214/215/216): REAL animated-GIF decode.
//
// Replaces the S68-era EXPLICIT-UNSUPPORTED GIF branch in decode_image_bytes
// (named errors still preserved for corrupt containers — §13 law). Frame
// data shares the RLottieDecoder uint32 layout so animation consumers use
// ONE representation. Laws: GIF89a GCE disposal 0/1/2/3 (see gif_decoder.cpp
// for the full source-first provenance).
#ifndef MINIANDROID_GIF_DECODER_H
#define MINIANDROID_GIF_DECODER_H

#include "software_renderer.h"  // DecodedImage

#include <cstdint>
#include <vector>

namespace miniandroid {
namespace renderer {

struct DecodedGif {
    int width = 0;
    int height = 0;
    int total_frames = 0;
    std::vector<int> delays_ms;         // per frame, GIF centiseconds -> ms
    std::vector<uint32_t> frames_rgba;  // width*height per frame, concatenated
    bool ok = false;
    std::string error;
};

class GifDecoder {
public:
    // First composited frame (static consumers). Named error on corrupt data.
    static bool decode_first_frame(const std::vector<uint8_t>& bytes,
                                   DecodedImage* out);
    // All frames (animation consumers). max_frames <= 0 = all frames.
    static bool decode_anim(const std::vector<uint8_t>& bytes, int max_frames,
                            DecodedGif* out);
};

}  // namespace renderer
}  // namespace miniandroid

#endif  // MINIANDROID_GIF_DECODER_H
