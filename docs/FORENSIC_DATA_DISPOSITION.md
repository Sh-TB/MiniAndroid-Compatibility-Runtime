# Forensic raw-dump disposition (#587 R27)

```json
{
 "what": "forensic_data/ raw GitHub API export snapshots removed from the tracked tree (#587 R27-4)",
 "date": "2026-11-13",
 "canonical_results_retained": [
  "docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl (390 normalized request rows \u2014 THE canonical audit artifact)",
  "docs/FORENSIC_LEDGER_STATS.json (recomputed from the ledger by scripts/forensic_ledger.py validate)"
 ],
 "generator_modes": {
  "validate (default)": "validates the checked-in ledger + recomputes stats; no raw dumps, no network, CI-safe \u2014 proven: 390 rows, 0 errors",
  "rebuild [dir]": "full historical reconstruction from raw dumps; proven to run end-to-end (390 rows emitted); reproduces the ledger as-of the registry state at generation time; current-main registry drift documented, as-of-state recoverable from git history",
  "fetch": "explicit online acquisition into gitignored .cache/forensics/<snapshot-id>/ then rebuild; token via git credential store only"
 },
 "patch_triage_R27_1": {
  "forensic_data/ar5_patch/part1.diff": "MERGED \u2014 A-R5 CLASS-INFO PROTO FALLBACK LAW present at miniandroid/src/dex/dalvik_engine.cpp:2900 (S218 V2 fix)",
  "forensic_data/ar5_patch/part2.diff": "MERGED \u2014 Makefile LAWS130 target + framework shadow changes present in main",
  "forensic_data/ar5_patch/part3.diff": "MERGED \u2014 miniandroid/tests/r25_dispatch_matrix_test.cpp exists and PASSES in make test-all (28/28)"
 },
 "removed_files": [
  {
   "path": "forensic_data/all_issue_comments.json.gz",
   "bytes": 2018897,
   "sha256": "58c9f8cf7a38e52ce323932141747c836663176fffbb9e0894588fed94843d09"
  },
  {
   "path": "forensic_data/ar5_patch/part1.diff",
   "bytes": 15067,
   "sha256": "ea0da04e9d89c890dd683d2fc2124870588de4b014f2587e7ffc14a2f6e0445a"
  },
  {
   "path": "forensic_data/ar5_patch/part2.diff",
   "bytes": 37406,
   "sha256": "14c37152e3c39261c00f9ca113750b1b3fd7bc6cc4ba64975d4aaa5425f71c49"
  },
  {
   "path": "forensic_data/ar5_patch/part3.diff",
   "bytes": 22699,
   "sha256": "be335488d5147a11cc0519d4c967d50ae85b5be24e243925e133183318376f75"
  },
  {
   "path": "forensic_data/batch367/evidence_map_full.json",
   "bytes": 101991,
   "sha256": "263d6052b3281cf661b36bd24dd6b4bbb6fff63e979f69bccdf95e60c5618ff7"
  },
  {
   "path": "forensic_data/batch367/evidence_map_raw.json",
   "bytes": 102311,
   "sha256": "f8ca8a71249ebac0687bd02777d0967675dc3c785d595f9577630c92aebddcc8"
  },
  {
   "path": "forensic_data/batch367/issue_1.json",
   "bytes": 14571,
   "sha256": "2fdb1408d945e90905e0fd37e20340f716d1601dc1d1cb1ea78194b262d94167"
  },
  {
   "path": "forensic_data/batch367/issue_10.json",
   "bytes": 6901,
   "sha256": "9476a58d5ff1003df94193d93afd8bd172f723cdaad0c771bfb7d8c250102fa3"
  },
  {
   "path": "forensic_data/batch367/issue_10_comments.json",
   "bytes": 9013,
   "sha256": "5cbe2b77249463757b80bffb6def61fa58d43eda23634604de3c1d34e9a24d2e"
  },
  {
   "path": "forensic_data/batch367/issue_11.json",
   "bytes": 7025,
   "sha256": "19e2b06a56258c965b287ed6aca48e4822404b788f5898d4c678c7a594bc5683"
  },
  {
   "path": "forensic_data/batch367/issue_11_comments.json",
   "bytes": 9496,
   "sha256": "fc691dbacb979b948e92ea5ac0864efbc04b8650a3bfb82c018c1b93c1e9d2e6"
  },
  {
   "path": "forensic_data/batch367/issue_12.json",
   "bytes": 6980,
   "sha256": "5996ce100875c91c8c16965e28b50389d0aefba5144ae281f40c8854799b3397"
  },
  {
   "path": "forensic_data/batch367/issue_121.json",
   "bytes": 8222,
   "sha256": "fe85e35d511834d27291dd276ce9af012f2a2fd4d17c866e019529ecbc7e5a52"
  },
  {
   "path": "forensic_data/batch367/issue_121_comments.json",
   "bytes": 5781,
   "sha256": "a6da4fdc63dc00087fd399aa7b1e1f83a7135c5f95f0e0d705f9adebdaacef11"
  },
  {
   "path": "forensic_data/batch367/issue_12_comments.json",
   "bytes": 9152,
   "sha256": "63243b1f07d8e5639db01d4d579b0d0a35686170c10dc62453060727feaf5733"
  },
  {
   "path": "forensic_data/batch367/issue_13.json",
   "bytes": 9256,
   "sha256": "b89c0c9d3ae154b1141491f949dc61108cd05c499376d2a1f0bd90e14e05d795"
  },
  {
   "path": "forensic_data/batch367/issue_13_comments.json",
   "bytes": 14980,
   "sha256": "d03ba56f5bc717f6438126f20e935c686539f4888e3062faca9e81eb872cea60"
  },
  {
   "path": "forensic_data/batch367/issue_15.json",
   "bytes": 6539,
   "sha256": "7c7c98979530bc754a61695626d194cbf56184e2560b92ced4b20a60cc8cae39"
  },
  {
   "path": "forensic_data/batch367/issue_15_comments.json",
   "bytes": 11905,
   "sha256": "fbe1f6132c8710b56d402c4c18f8d96e52ebf72b01124f6045383719ac8b87f0"
  },
  {
   "path": "forensic_data/batch367/issue_166.json",
   "bytes": 8228,
   "sha256": "c0ec75b24ef76d1ab9ed33532899e95198ddf3b5be9d643c529591ec9e7d7b6c"
  },
  {
   "path": "forensic_data/batch367/issue_166_comments.json",
   "bytes": 5657,
   "sha256": "2879510b5528f81e106c86e6d0aa62d2e2b645d83a48654c630db63416dbf896"
  },
  {
   "path": "forensic_data/batch367/issue_17.json",
   "bytes": 6203,
   "sha256": "91c8047754787ad35b7aed9dd9a1e59c8ee6fa16abacdf90898e33c01cb09e2e"
  },
  {
   "path": "forensic_data/batch367/issue_17_comments.json",
   "bytes": 11848,
   "sha256": "a055a596a01cb0cd8550b3ba466e5fe05b4a8c00f9788451b0e63959fc3e3db8"
  },
  {
   "path": "forensic_data/batch367/issue_18.json",
   "bytes": 5859,
   "sha256": "c3d07429b44695ce5fc78849e8ab2209688225518947530a7696120b4d1c0c15"
  },
  {
   "path": "forensic_data/batch367/issue_18_comments.json",
   "bytes": 11435,
   "sha256": "c91d6768bcd92a2c6a92ac7e45186b9f2b6c58e6eb2a80889d91fb39fb3d7c87"
  },
  {
   "path": "forensic_data/batch367/issue_1_comments.json",
   "bytes": 7934,
   "sha256": "c1d3e0e1cf25844e38386a953e4536145ae8e155c5a269ba39c74b68aed322aa"
  },
  {
   "path": "forensic_data/batch367/issue_2.json",
   "bytes": 13051,
   "sha256": "189f8b4de323a3c7ce76e988c53be56ce6f88f96d90365568eea689fa2fbebd2"
  },
  {
   "path": "forensic_data/batch367/issue_234.json",
   "bytes": 5399,
   "sha256": "5f9ce181bb9db8e278f99627c9bcbf6fb797a9e40824d4b19df3c950577608e7"
  },
  {
   "path": "forensic_data/batch367/issue_234_comments.json",
   "bytes": 2664,
   "sha256": "64c298c66f55afd1964a82088f13957d9d3cb191c332136c440be6c98c5c91da"
  },
  {
   "path": "forensic_data/batch367/issue_235.json",
   "bytes": 5365,
   "sha256": "21d03bd4cf5c27fda74ab5e3611e3fa15368cedef57009fd475268a131526881"
  },
  {
   "path": "forensic_data/batch367/issue_235_comments.json",
   "bytes": 2834,
   "sha256": "050fac13e5f571d980d29c06ab072ce5baff2983ceffc24a193414d3b715f6bf"
  },
  {
   "path": "forensic_data/batch367/issue_236.json",
   "bytes": 5385,
   "sha256": "31f81df5f4f35a42e3c8ca010270d888ca1efee691845818d1ba1f440a2728bf"
  },
  {
   "path": "forensic_data/batch367/issue_236_comments.json",
   "bytes": 2385,
   "sha256": "deafb1b958329fe077ff6311703cbbd3fddbb605ee1a77d00f3bcfb77d53e0c2"
  },
  {
   "path": "forensic_data/batch367/issue_237.json",
   "bytes": 5373,
   "sha256": "241811d56278e5e58c6e733daa8e3964d0abed8e71fab6dd14005cea35fa6cb4"
  },
  {
   "path": "forensic_data/batch367/issue_237_comments.json",
   "bytes": 2389,
   "sha256": "261077f1fdf3f64efb02433aed97d7b82ef47207440795fddea057894959bd1d"
  },
  {
   "path": "forensic_data/batch367/issue_238.json",
   "bytes": 5367,
   "sha256": "7facd5583f0bfd04fc2ccec75d9331737cb89eb22274c0f2b98591e6ecb3a2ba"
  },
  {
   "path": "forensic_data/batch367/issue_238_comments.json",
   "bytes": 2404,
   "sha256": "5f18fc7489212f57cc301d1475a4feca275711688f58f06b24a3760b19044aa8"
  },
  {
   "path": "forensic_data/batch367/issue_239.json",
   "bytes": 5367,
   "sha256": "51e3ff1d1bc4e4383e004d3272639c3c73e4646a1ef8e14ebb87eb4d2f1ac11f"
  },
  {
   "path": "forensic_data/batch367/issue_239_comments.json",
   "bytes": 2550,
   "sha256": "f1d138d01aa6c8eaf183236dad2661591f7e55789a457aa53b75a11b9a51b4e5"
  },
  {
   "path": "forensic_data/batch367/issue_240.json",
   "bytes": 5369,
   "sha256": "1fa0b4ea8a06d15148b5f3dd73de0fbb3f979f69cb4010fe63db3aff0374207c"
  },
  {
   "path": "forensic_data/batch367/issue_240_comments.json",
   "bytes": 2393,
   "sha256": "ae35454a4c35ed32b22c682fd81e2eb5dfc69cbfe06344a3ff6cabf9e304fc0e"
  },
  {
   "path": "forensic_data/batch367/issue_241.json",
   "bytes": 5381,
   "sha256": "ce73d5d1b880d6a3fcdb45335a8949fec44d0bf4feec10bcbf67d32584580115"
  },
  {
   "path": "forensic_data/batch367/issue_241_comments.json",
   "bytes": 2702,
   "sha256": "60a4a680863ae76fcc85658318ca95f8c55da6cff0e9867142e5c0f2a4d8b964"
  },
  {
   "path": "forensic_data/batch367/issue_242.json",
   "bytes": 5394,
   "sha256": "69d842e8129479ff23ddb163824d13d187202d579874ba984f1f7742160118a4"
  },
  {
   "path": "forensic_data/batch367/issue_242_comments.json",
   "bytes": 3257,
   "sha256": "ff11d76ed28ed3ed9d234b5e2afcaa185751912037347b9e85e937d57365a4a3"
  },
  {
   "path": "forensic_data/batch367/issue_243.json",
   "bytes": 5370,
   "sha256": "115e80ea4a383a1a0f1c8f06cc25f626d7285ae639c7d3b7ff2e1d1af24bd567"
  },
  {
   "path": "forensic_data/batch367/issue_243_comments.json",
   "bytes": 2718,
   "sha256": "e0f4b40f9816871585f1ba58fb0e2290646cb631634596688ed0f5bd25dc2b9e"
  },
  {
   "path": "forensic_data/batch367/issue_244.json",
   "bytes": 5368,
   "sha256": "7d63043e6d1cd0dff99082d6d3e1719b703a51d47d1f1e0a40a73bb1e59c05d9"
  },
  {
   "path": "forensic_data/batch367/issue_244_comments.json",
   "bytes": 2489,
   "sha256": "8d1a798d0b95663f58b6434ad144cd1f291552c94d3f7d1fc6d871f8e266be4c"
  },
  {
   "path": "forensic_data/batch367/issue_245.json",
   "bytes": 5368,
   "sha256": "2c81d684d6b03d0870adfaa23aa80abd035c80a79838c66baae32b608bea4371"
  },
  {
   "path": "forensic_data/batch367/issue_245_comments.json",
   "bytes": 2375,
   "sha256": "bb0daa9d42921dd7600d6c787fe98bd6a2e785b8dd31edda0b8ffe7e0f38dc23"
  },
  {
   "path": "forensic_data/batch367/issue_246.json",
   "bytes": 5356,
   "sha256": "e0923f47319570cc98ce7ce81fd3584a9d1c9b69ad23ecfa961c9115aa1c972f"
  },
  {
   "path": "forensic_data/batch367/issue_246_comments.json",
   "bytes": 2458,
   "sha256": "4c9498d3f18e5702e1b47e37e5f9f89a9e1d00b5936006246afbb679a1e941c9"
  },
  {
   "path": "forensic_data/batch367/issue_247.json",
   "bytes": 5356,
   "sha256": "b8eddbfb2fa6eb06ddff3bc5f733ae85f704aca01df68435581bd1aa3ea80110"
  },
  {
   "path": "forensic_data/batch367/issue_247_comments.json",
   "bytes": 2316,
   "sha256": "325395b181027cb26551ed6dd4fbe6a102b27270b729fe53f21d63407177c099"
  },
  {
   "path": "forensic_data/batch367/issue_248.json",
   "bytes": 5360,
   "sha256": "07f260b1fbba5422c2090c59db2cfdf26279d0c414faf0f6df5c8b07274f22d5"
  },
  {
   "path": "forensic_data/batch367/issue_248_comments.json",
   "bytes": 2328,
   "sha256": "0a217477e18c2c8ac3b29797aff9b3aaf4cf9c170d41148b449c904fba79dc35"
  },
  {
   "path": "forensic_data/batch367/issue_249.json",
   "bytes": 5354,
   "sha256": "6892aa3623a5283cf6b3e1e80b3491bbbe12aa7defc74ac01544b004a7a41750"
  },
  {
   "path": "forensic_data/batch367/issue_249_comments.json",
   "bytes": 2304,
   "sha256": "fdc7bf3e15b0141634c9b2affa70715fe3bdca64be9b596657e15334802c7284"
  },
  {
   "path": "forensic_data/batch367/issue_250.json",
   "bytes": 5422,
   "sha256": "7db96f6449b086270476aa020c584e09afe7dc86787c53f720ce321d28ae04b4"
  },
  {
   "path": "forensic_data/batch367/issue_250_comments.json",
   "bytes": 2500,
   "sha256": "bda609f3a38720544e42a40ab71e2a13e5886a977743b3159e383966af2c0c30"
  },
  {
   "path": "forensic_data/batch367/issue_251.json",
   "bytes": 5384,
   "sha256": "13e95187dfde67165dee2105e6e7c178ede452bc7b0d5bef41d9ef7f25003f89"
  },
  {
   "path": "forensic_data/batch367/issue_251_comments.json",
   "bytes": 2489,
   "sha256": "4f9c6ec6cd457cd5d1886b1c51958c8c0b1c6fce6e4b80e20acbeb5c9a8be959"
  },
  {
   "path": "forensic_data/batch367/issue_252.json",
   "bytes": 5400,
   "sha256": "d15c6f73ccc00d98411664359cad144add778bd7eb4fe5e700b533b54329cfdf"
  },
  {
   "path": "forensic_data/batch367/issue_252_comments.json",
   "bytes": 2493,
   "sha256": "d57ecdb1ad8f9b063f896f9f5caf0b3f3a9010cd0e482d2256924203e51afd35"
  },
  {
   "path": "forensic_data/batch367/issue_253.json",
   "bytes": 5392,
   "sha256": "6c01f68e3853f5add71afa1bb2a4be3ac46473d2699333ecfffd0e6b74eedff8"
  },
  {
   "path": "forensic_data/batch367/issue_253_comments.json",
   "bytes": 2487,
   "sha256": "a048d5e2b06be4ddd36140e9acd912eb127a83d7d86ecbb80d9a1d01aa50120d"
  },
  {
   "path": "forensic_data/batch367/issue_254.json",
   "bytes": 5394,
   "sha256": "2f9aa551819e803215ebdd1d2c9c7bb9e9011898ec7c3ac94ebce5a193020d8f"
  },
  {
   "path": "forensic_data/batch367/issue_254_comments.json",
   "bytes": 2488,
   "sha256": "53bea25d53e29c38fc0da2989d1143ab37a2bd4a4e94f1b80bfbc1c627fd4ce5"
  },
  {
   "path": "forensic_data/batch367/issue_255.json",
   "bytes": 5396,
   "sha256": "5b79a8b1eef3721f6656925bbab99ca244190cd404fb954abca2280733225dcf"
  },
  {
   "path": "forensic_data/batch367/issue_255_comments.json",
   "bytes": 2474,
   "sha256": "58b0d814ca91da1fe861b5fd9e394b12e161943b54afae182414090154176e69"
  },
  {
   "path": "forensic_data/batch367/issue_256.json",
   "bytes": 5398,
   "sha256": "d178a0c90dd29e3b0c1fee87c925151736dca083ce60f97911a53f2a229c0016"
  },
  {
   "path": "forensic_data/batch367/issue_256_comments.json",
   "bytes": 2537,
   "sha256": "db00a79090ae75f3bc5b008066ae92b2f0baa8f02d65dedb2e62ebfa071ba425"
  },
  {
   "path": "forensic_data/batch367/issue_257.json",
   "bytes": 5386,
   "sha256": "37ed6a433a239c29a007f9d1885c05f56e663fb8afed13526252cb4f6fc41066"
  },
  {
   "path": "forensic_data/batch367/issue_257_comments.json",
   "bytes": 2514,
   "sha256": "33e87b2961ddabe7b5060cc43e55eec9ac74b8bf0f108529371f97be69aca637"
  },
  {
   "path": "forensic_data/batch367/issue_258.json",
   "bytes": 5388,
   "sha256": "6a7f2aed79971e96867c8f41f5b516ead44b5cf924484ed08646321b97e110a5"
  },
  {
   "path": "forensic_data/batch367/issue_258_comments.json",
   "bytes": 2511,
   "sha256": "fa59580b4cf1d27338cfb33aeb57e21933e98dea64997350d5b687c395b0b9b6"
  },
  {
   "path": "forensic_data/batch367/issue_259.json",
   "bytes": 5374,
   "sha256": "8f6afbd56502b8548b2a247fa9601f911073599baba97f688d16e51a5e9f54f5"
  },
  {
   "path": "forensic_data/batch367/issue_259_comments.json",
   "bytes": 2499,
   "sha256": "3961fb14249c0d28e9a94e4470037367c330ec50b7e3d84be47644141da8aa21"
  },
  {
   "path": "forensic_data/batch367/issue_260.json",
   "bytes": 5372,
   "sha256": "b62279795d0d4a8725ebf80de5be27e04eed1cb0fa524a19b5960bc722be32fb"
  },
  {
   "path": "forensic_data/batch367/issue_260_comments.json",
   "bytes": 2489,
   "sha256": "28a9eab616ea014ecefb244a4a4838293a1afae61faa58cc61bcb04c905260fe"
  },
  {
   "path": "forensic_data/batch367/issue_261.json",
   "bytes": 5378,
   "sha256": "cb718c39b75bd05b2248bba87f0f5faaf14d9caa9c90b58ffc2ecd2827e16b27"
  },
  {
   "path": "forensic_data/batch367/issue_261_comments.json",
   "bytes": 2495,
   "sha256": "a0730f7b3560b8dd64d491463d3bd3c770275171c9b395ce2cc763c2d74a7de4"
  },
  {
   "path": "forensic_data/batch367/issue_262.json",
   "bytes": 5422,
   "sha256": "d6e0bf2bfeb31f72bba04ea4d9414dd8ca0fb7c7e2437fc7f83cb668dfafc0e2"
  },
  {
   "path": "forensic_data/batch367/issue_262_comments.json",
   "bytes": 2520,
   "sha256": "32bfc0acc92ea6f89bde5e21ccae22ad8d2a745ce9a4dbd9457d13f3a2700c36"
  },
  {
   "path": "forensic_data/batch367/issue_263.json",
   "bytes": 5562,
   "sha256": "f87780c799031dfd595c8370e6e97150f9a7242de33b7158faffc84f68fd3db7"
  },
  {
   "path": "forensic_data/batch367/issue_263_comments.json",
   "bytes": 3166,
   "sha256": "34a4c4b3caf840deb05021c9ac06979fb9936b42998a40f3c4c9fcfe73ef9bc3"
  },
  {
   "path": "forensic_data/batch367/issue_264.json",
   "bytes": 5574,
   "sha256": "c3b8372110c8af4b90ad953e3df969901947f917c9f9e2b30141dd2e3168b94a"
  },
  {
   "path": "forensic_data/batch367/issue_264_comments.json",
   "bytes": 3173,
   "sha256": "e5f1b38f874da3cf83de4c98931738d405190a54d385f12f7bc61eb58d822dc6"
  },
  {
   "path": "forensic_data/batch367/issue_265.json",
   "bytes": 5570,
   "sha256": "304129562e3dcf5f91ffcfad63542df9250b89c24b9ab88a14bbd38cad0af475"
  },
  {
   "path": "forensic_data/batch367/issue_265_comments.json",
   "bytes": 3216,
   "sha256": "b23222e5f42eaa37f3ac0ccead425bc6b33fd99116608991dbe966a3b04d2fa7"
  },
  {
   "path": "forensic_data/batch367/issue_266.json",
   "bytes": 5379,
   "sha256": "419b70d91f0a636b102c1480e13fb4e95718b84215cb80a9c42f385ae6bcdb87"
  },
  {
   "path": "forensic_data/batch367/issue_266_comments.json",
   "bytes": 3133,
   "sha256": "bd38c79d87d9e697ccbb7aa48ec0a4988e0b51037c11f9ab450977e1e02e905f"
  },
  {
   "path": "forensic_data/batch367/issue_267.json",
   "bytes": 5602,
   "sha256": "5751afb8699333535b3c2188fdcdea2c29b2c6b30a5c3731e246246f18f1e4b9"
  },
  {
   "path": "forensic_data/batch367/issue_267_comments.json",
   "bytes": 2899,
   "sha256": "abc374082756f1ecde790be512a774c275c5930e81b4397a6fdf6447952570bc"
  },
  {
   "path": "forensic_data/batch367/issue_268.json",
   "bytes": 5602,
   "sha256": "731de2236374f819b2ad1e714d98ddb0a154e11f77536cc99d3317e92ef1dd5a"
  },
  {
   "path": "forensic_data/batch367/issue_268_comments.json",
   "bytes": 2942,
   "sha256": "f25f99f796874921f87ef451207e538e0af375c1f04c76d4c6e7f652d4af1972"
  },
  {
   "path": "forensic_data/batch367/issue_269.json",
   "bytes": 5399,
   "sha256": "eb930c59b6a2f4db7a5e9e83030c5e64f12dce1d6e98d4cbe221c096e7c3f72c"
  },
  {
   "path": "forensic_data/batch367/issue_269_comments.json",
   "bytes": 2939,
   "sha256": "d3d76c11a2520527ccc9133b4899567bf0168b196d90ae74ce2c2603bbcd8ff9"
  },
  {
   "path": "forensic_data/batch367/issue_270.json",
   "bytes": 5381,
   "sha256": "41fe148e410d3ec2a6a3e0c5a616ab7f7e7d441d076b4d41ee35e2b5772bb603"
  },
  {
   "path": "forensic_data/batch367/issue_270_comments.json",
   "bytes": 2933,
   "sha256": "7f73849ebacc5d901366377cd4bd1e65fa960c157d5e19e9e01fe0f66fa5fc09"
  },
  {
   "path": "forensic_data/batch367/issue_273.json",
   "bytes": 5369,
   "sha256": "3750933993102b7e71702d17b48699ed4ff4002a77329386cb1f3a5f78cf5609"
  },
  {
   "path": "forensic_data/batch367/issue_273_comments.json",
   "bytes": 2916,
   "sha256": "5f7b08d3b62c35d0d96480825e1e352c20cc29925b20d460605e5ec8e0819bb6"
  },
  {
   "path": "forensic_data/batch367/issue_274.json",
   "bytes": 5383,
   "sha256": "1d56b9e9367a1080c1817ea64d6c7a38570d78685bc13b4d1025ddc7bbd7ba17"
  },
  {
   "path": "forensic_data/batch367/issue_274_comments.json",
   "bytes": 2914,
   "sha256": "948b1bad94ff2a7ab740c68e10a0c843a7448648b619edf060f5ee5d49a25aea"
  },
  {
   "path": "forensic_data/batch367/issue_275.json",
   "bytes": 5375,
   "sha256": "3e23c014af292bd47714a38da3b9b256297111613537dce472460eec237c79b3"
  },
  {
   "path": "forensic_data/batch367/issue_275_comments.json",
   "bytes": 2884,
   "sha256": "6e56003ea3ee48cacb4769fa4f81520a1be79559d477b8e6b987ef32c7d28307"
  },
  {
   "path": "forensic_data/batch367/issue_276.json",
   "bytes": 5377,
   "sha256": "62b4dc822988238bbefc0b2f0b4e49ca8167ddb2fda9419b4754274878ae4f2d"
  },
  {
   "path": "forensic_data/batch367/issue_276_comments.json",
   "bytes": 2853,
   "sha256": "88a44526d661e0b739beca1cdbcd8763dea00ab8a724c930664e6a4c0ad2fa06"
  },
  {
   "path": "forensic_data/batch367/issue_277.json",
   "bytes": 5385,
   "sha256": "469d37b4dae66a1fcab8d02c23511389283bd2f8d644c8053717737682923ef2"
  },
  {
   "path": "forensic_data/batch367/issue_277_comments.json",
   "bytes": 2880,
   "sha256": "45d59cbb1ce57ccf60ff44ba6461d9fdc6fe72b7ee1b2625422d9e54dc415727"
  },
  {
   "path": "forensic_data/batch367/issue_279.json",
   "bytes": 5363,
   "sha256": "fb1cc9bf132a0263100a9ab7f08c59e656f6bdcbcdbae28cea95b2911a49cc44"
  },
  {
   "path": "forensic_data/batch367/issue_279_comments.json",
   "bytes": 3063,
   "sha256": "6b390e7354306d00eab945389b1543fa03855bfd1a8fffb8ade6ff3cc4d056aa"
  },
  {
   "path": "forensic_data/batch367/issue_280.json",
   "bytes": 5367,
   "sha256": "8b36accff6316e587b8e8687bf06f0627beaa0b29d3d571a65181127b7d9fe78"
  },
  {
   "path": "forensic_data/batch367/issue_280_comments.json",
   "bytes": 2912,
   "sha256": "60ed376a7bd09802693cd7bdb63bd0cff3f2f27344a75450926b3cd1c5238c6c"
  },
  {
   "path": "forensic_data/batch367/issue_285.json",
   "bytes": 5423,
   "sha256": "f99e8519fefef042d9caa2ba74a719189bef24d9b9d6f3be0d0111604992b9a9"
  },
  {
   "path": "forensic_data/batch367/issue_285_comments.json",
   "bytes": 2927,
   "sha256": "dd214b552a4b1f66e56dcadfff21e36198b53a7c43de9ae8006900dcc1e38f8c"
  },
  {
   "path": "forensic_data/batch367/issue_286.json",
   "bytes": 5409,
   "sha256": "e7ed66c9712bf582ec4eba33e884e49c361e8a8993f60008a953c321b76a3719"
  },
  {
   "path": "forensic_data/batch367/issue_286_comments.json",
   "bytes": 2939,
   "sha256": "5057b98d135c609c56be3e68fec9c046bd830fe80d037badec23822ee78a89ff"
  },
  {
   "path": "forensic_data/batch367/issue_287.json",
   "bytes": 5421,
   "sha256": "0e9b97abf02d8e9cda9e08a0089100e002ce218da5bb358e12cc2f040d2fb76c"
  },
  {
   "path": "forensic_data/batch367/issue_287_comments.json",
   "bytes": 3029,
   "sha256": "4c5f64427cf604202c4f4ce608180fdb4d05348341e58d2237ba18bc4b7c2fd8"
  },
  {
   "path": "forensic_data/batch367/issue_289.json",
   "bytes": 5404,
   "sha256": "34afe7975c86ba2fabda987d19e0eb7751cf71b01592f39f070985c28c10c839"
  },
  {
   "path": "forensic_data/batch367/issue_289_comments.json",
   "bytes": 2836,
   "sha256": "9afc65b21a691a460cd541d21aeb5e1dcc16a7c125c96acfbf7de53fb6c0c0ca"
  },
  {
   "path": "forensic_data/batch367/issue_291.json",
   "bytes": 5538,
   "sha256": "2bb4118086b8b29e7c88cf635e0823681d6eb0637b23bf6241b6273aedeac34d"
  },
  {
   "path": "forensic_data/batch367/issue_291_comments.json",
   "bytes": 3077,
   "sha256": "9c6c4bc4901002a82f6034e1c386f0744b71ed76c9b9f82b75cc770e8a6d5c93"
  },
  {
   "path": "forensic_data/batch367/issue_292.json",
   "bytes": 5516,
   "sha256": "d12dd912e9d5ea1e658e942d4fdc75ccad882d77224e1f9f07be16c15f0627f7"
  },
  {
   "path": "forensic_data/batch367/issue_292_comments.json",
   "bytes": 2891,
   "sha256": "4073b95e5acf4f81b3b75e8af7b616d34e8339e71a443eee496912cda16ee3b3"
  },
  {
   "path": "forensic_data/batch367/issue_293.json",
   "bytes": 5514,
   "sha256": "ec449557020e22b9c0b8f1101be171d94bbcb95e561265612f30f379fd7d1aff"
  },
  {
   "path": "forensic_data/batch367/issue_293_comments.json",
   "bytes": 2930,
   "sha256": "dfe868b8701b76f67a69d1fa115fcc47d49c2906ad1fb149fc04cb07ad093dc6"
  },
  {
   "path": "forensic_data/batch367/issue_294.json",
   "bytes": 5522,
   "sha256": "59eb16b0a72f5040d48d249ccd58587e4041f09c81aa38878ec6d398cfe9379e"
  },
  {
   "path": "forensic_data/batch367/issue_294_comments.json",
   "bytes": 3241,
   "sha256": "afbffc848c52b9e967b56cc895438361440d4a0f98f97b3dfd885025a4a248ff"
  },
  {
   "path": "forensic_data/batch367/issue_298.json",
   "bytes": 5529,
   "sha256": "97e2041d74a42597024c01385a88d25f487955fd47749b03ee800145a499afb8"
  },
  {
   "path": "forensic_data/batch367/issue_298_comments.json",
   "bytes": 2971,
   "sha256": "fc83417a993a893a9da1ae870972ba37167b2fd1b94f7ae17eaecfa6096f7218"
  },
  {
   "path": "forensic_data/batch367/issue_299.json",
   "bytes": 5519,
   "sha256": "48c0efe8193e660e8f784e79e82b000907d510c61e11b64ad3df61e7bcf0e8c3"
  },
  {
   "path": "forensic_data/batch367/issue_299_comments.json",
   "bytes": 2914,
   "sha256": "186fd20bbbc7d7f6c5fc61966094de07975a12c3187775555d88fe8bb71789bc"
  },
  {
   "path": "forensic_data/batch367/issue_2_comments.json",
   "bytes": 7450,
   "sha256": "a5c569eb0f87beb93c5720ec7e718331639917c93fa387d762f89a712fded085"
  },
  {
   "path": "forensic_data/batch367/issue_3.json",
   "bytes": 11746,
   "sha256": "abf79dc9faba58b43d5143a97c621508f6a825badf8fae141ab43b0787da0609"
  },
  {
   "path": "forensic_data/batch367/issue_300.json",
   "bytes": 5513,
   "sha256": "36be00cc0ccbdbb347a89683bbf2ce9ad3e85c0a820411cc046eb6336f96d748"
  },
  {
   "path": "forensic_data/batch367/issue_300_comments.json",
   "bytes": 2874,
   "sha256": "0eb275237e0db451a233acc1f73aa71c942275173553ad88537fd3a5fe2c41d8"
  },
  {
   "path": "forensic_data/batch367/issue_301.json",
   "bytes": 5525,
   "sha256": "b1e0fbf06bbfdecd43cb448e9d7de89842c0517676fe82161c89a589f124dc1e"
  },
  {
   "path": "forensic_data/batch367/issue_301_comments.json",
   "bytes": 2900,
   "sha256": "704533386ce64919718903c3855196fee13c4f49f30acdfb54dbb6651dc28ae0"
  },
  {
   "path": "forensic_data/batch367/issue_302.json",
   "bytes": 5537,
   "sha256": "6828e4eb133c08e0878a2de1117c71bf12f8b1abbc4a0acf3f17aede837c85ee"
  },
  {
   "path": "forensic_data/batch367/issue_302_comments.json",
   "bytes": 2964,
   "sha256": "b01b88dc661bf53ad36ae3e98e89a5627aa086e7428b0667b8366f085c71b90a"
  },
  {
   "path": "forensic_data/batch367/issue_303.json",
   "bytes": 5516,
   "sha256": "d2f2b426abb9441f93566e5cbfc52d8eef5fec73b1d90b7d2d7ea5ae3a383285"
  },
  {
   "path": "forensic_data/batch367/issue_303_comments.json",
   "bytes": 3118,
   "sha256": "64fbe6190f85d6bea60803b65c75204e8cac40b8fc89f6661065f30cf8807b4a"
  },
  {
   "path": "forensic_data/batch367/issue_305.json",
   "bytes": 5529,
   "sha256": "fddaf353bae78588b96717e95b36156f13181eb46d0e1fc4653545728a303536"
  },
  {
   "path": "forensic_data/batch367/issue_305_comments.json",
   "bytes": 2946,
   "sha256": "d5cc5f5ab86d4be645d6fd32ca5b94bfa1b4f59a1043e3b943606e5f8742c1bb"
  },
  {
   "path": "forensic_data/batch367/issue_306.json",
   "bytes": 5523,
   "sha256": "073af287cb637e587f55797c447258d30c41f27ce0b819c50fb885d63f4d72d4"
  },
  {
   "path": "forensic_data/batch367/issue_306_comments.json",
   "bytes": 2922,
   "sha256": "87f7a4650b96ed0ed7221f89eed9a36db4984d8a048a3997ad98e561e1a24310"
  },
  {
   "path": "forensic_data/batch367/issue_307.json",
   "bytes": 5601,
   "sha256": "988488bdeea200adb47e71e0a12fc7202416f3ec0fd6f6ede084683494573091"
  },
  {
   "path": "forensic_data/batch367/issue_307_comments.json",
   "bytes": 2916,
   "sha256": "85319eda127dc6833054398dcce3a2e1d685ff0ef90cdfca41b28a2d50265afc"
  },
  {
   "path": "forensic_data/batch367/issue_308.json",
   "bytes": 5601,
   "sha256": "ea4928338bd802b0aa723b5d47d0660cd50b5cbf9d77722834b226eb8ead9ed2"
  },
  {
   "path": "forensic_data/batch367/issue_308_comments.json",
   "bytes": 2895,
   "sha256": "48a0dbef3df44a6552801e6d953db4a5799db01dd1f1df979eb1211b5d4321e2"
  },
  {
   "path": "forensic_data/batch367/issue_309.json",
   "bytes": 5599,
   "sha256": "8a03abdb0da9d8ad6fa91b72655b0aece89c632b68b771ee4b3589ad41836c9a"
  },
  {
   "path": "forensic_data/batch367/issue_309_comments.json",
   "bytes": 3067,
   "sha256": "eb911ae1c9e96b01fcb656205cacda5f115fe2c51bb0b3164cc7ea636d3dab72"
  },
  {
   "path": "forensic_data/batch367/issue_310.json",
   "bytes": 5601,
   "sha256": "0f11badbb3612efb1bcc2b0930cbe53acba9bec3ce63714f4e0d109a4be76220"
  },
  {
   "path": "forensic_data/batch367/issue_310_comments.json",
   "bytes": 2972,
   "sha256": "0936968274443b1e170f961b9812bf3365c1040e73036234c49062ba1be01ad9"
  },
  {
   "path": "forensic_data/batch367/issue_313.json",
   "bytes": 5597,
   "sha256": "c51d7ffac539ae838cb8ecd7127b4e10f41f6a8bda1fe5cde7e30d4c00ac95c3"
  },
  {
   "path": "forensic_data/batch367/issue_313_comments.json",
   "bytes": 2982,
   "sha256": "b80db7c62bd0fffadbba53a79d3e63721422e097c0aa82de2869076d68214e6f"
  },
  {
   "path": "forensic_data/batch367/issue_314.json",
   "bytes": 5381,
   "sha256": "db8022713d86e05325c14bc15df39fd4722cfd7fbdf6458d9eddd2e152f45d0f"
  },
  {
   "path": "forensic_data/batch367/issue_314_comments.json",
   "bytes": 2991,
   "sha256": "a4ea1be621f85817e7133a13009cdae3ce0f443328fdcad1a19113e1b823146d"
  },
  {
   "path": "forensic_data/batch367/issue_315.json",
   "bytes": 5379,
   "sha256": "35697b2d696b5b16d14cd6505d4d9c4605c4fd5b623c1b53bfe13c5c932b4e6f"
  },
  {
   "path": "forensic_data/batch367/issue_315_comments.json",
   "bytes": 2968,
   "sha256": "dace4c0b61ccc4ed48e6ddc7aeeccab7fe70b875d100e96f3f242068745f0413"
  },
  {
   "path": "forensic_data/batch367/issue_316.json",
   "bytes": 5367,
   "sha256": "bdaf19bc3d3d20be14074c14ad629caeeb46d4bd7e76882dcd9600ce8a677de6"
  },
  {
   "path": "forensic_data/batch367/issue_316_comments.json",
   "bytes": 2936,
   "sha256": "3f2e8b67f7733a9ae06e5b7302d13261eefecff1f2d8ded371df171b07bfbe14"
  },
  {
   "path": "forensic_data/batch367/issue_317.json",
   "bytes": 5373,
   "sha256": "84c8ea87d4d0ff0b220c27793b592931a695109cf0b3d7ae0e2d781c5386e6e2"
  },
  {
   "path": "forensic_data/batch367/issue_317_comments.json",
   "bytes": 3271,
   "sha256": "313bb76a586a670f04710a7b0c871bcf70d85465abc1a4b78ccc6c1a790149da"
  },
  {
   "path": "forensic_data/batch367/issue_318.json",
   "bytes": 5377,
   "sha256": "86ad7a768978c3a0a3c315d6d08981dca5bde76a6371fdab2920a094a6a4b8f1"
  },
  {
   "path": "forensic_data/batch367/issue_318_comments.json",
   "bytes": 2930,
   "sha256": "94c8b709d76b81a7d215b098668da3a48df35a1afa20ad47424ae8b0ece19963"
  },
  {
   "path": "forensic_data/batch367/issue_319.json",
   "bytes": 5342,
   "sha256": "fa392125abdf8f300f8c2e1d5f05426fe1b505b23753630a18b729fd72e4c2ac"
  },
  {
   "path": "forensic_data/batch367/issue_319_comments.json",
   "bytes": 2917,
   "sha256": "f368802c0b773201d1b38b3c037de3c240eebd8bec7f07d7955b926f343c6d66"
  },
  {
   "path": "forensic_data/batch367/issue_321.json",
   "bytes": 5346,
   "sha256": "ca1423fdb4b8cf38ce7433d053fd5781818e8fcf9d493ef0c0c3a993168c297e"
  },
  {
   "path": "forensic_data/batch367/issue_321_comments.json",
   "bytes": 2887,
   "sha256": "08376b0d8b3e789b96251727e38fd7d98fb660a9b5f218a2097b8f04b291451f"
  },
  {
   "path": "forensic_data/batch367/issue_323.json",
   "bytes": 5349,
   "sha256": "af0331a962c550ee4cb60e2a608dfabe9126c84648fcacf13abafc2d75c2b0fb"
  },
  {
   "path": "forensic_data/batch367/issue_323_comments.json",
   "bytes": 3258,
   "sha256": "0d421644e469485623b29b7b0645d822ffde39be3803d5eb227c6c2da73265c2"
  },
  {
   "path": "forensic_data/batch367/issue_331.json",
   "bytes": 5422,
   "sha256": "f3d6e36bd6eefff98bbfdfecd4922fc67da1bb40cafe2eef4f88a1173569971e"
  },
  {
   "path": "forensic_data/batch367/issue_331_comments.json",
   "bytes": 3176,
   "sha256": "8536eaf92a67dec6286ffe52a494583078ffc1e494aaf1bec2e3029df07cf528"
  },
  {
   "path": "forensic_data/batch367/issue_332.json",
   "bytes": 5426,
   "sha256": "d918723f9c42be927270111f73d0c4353475008066f519c2cf7178fe35dc527d"
  },
  {
   "path": "forensic_data/batch367/issue_332_comments.json",
   "bytes": 3077,
   "sha256": "474d4780328eb9906e4cea28a7e8e897ea79b14f6822f1d3bb03582b26f55d88"
  },
  {
   "path": "forensic_data/batch367/issue_333.json",
   "bytes": 5418,
   "sha256": "52b9346814710f24907dcf83440974ea403c672c7c8bf5b9e74ac6149f17de70"
  },
  {
   "path": "forensic_data/batch367/issue_333_comments.json",
   "bytes": 2980,
   "sha256": "2569d509924c09124607f36a7a706a5b2f905d62898776c43689fa249d021e42"
  },
  {
   "path": "forensic_data/batch367/issue_334.json",
   "bytes": 4555,
   "sha256": "cd421e7772f5645a3e43b7e460a98b22a040a94b63eca69fd143216b50568e4d"
  },
  {
   "path": "forensic_data/batch367/issue_334_comments.json",
   "bytes": 2989,
   "sha256": "9218b945bfae279dfe56e90b3c8eb70d22e2eb591e8da0c836de3d4e001e6708"
  },
  {
   "path": "forensic_data/batch367/issue_335.json",
   "bytes": 4487,
   "sha256": "d65f374fde61af3c49c6fa18b1ed006871036b3c3cfec1cac0a382d609a68f3e"
  },
  {
   "path": "forensic_data/batch367/issue_335_comments.json",
   "bytes": 2095,
   "sha256": "0bc5aca19b1c3610b521d637988809262c7d23c7c04b9d464e6c05957b0c866a"
  },
  {
   "path": "forensic_data/batch367/issue_336.json",
   "bytes": 4410,
   "sha256": "22ed2e864b6641fbac1fa1466609e62b31e439b24ad0f8a91acd083b60945dc5"
  },
  {
   "path": "forensic_data/batch367/issue_336_comments.json",
   "bytes": 2254,
   "sha256": "a87942f73da47d59a7f577f55a74f2538dd5f2da8e0849906cd083955e3f9fd8"
  },
  {
   "path": "forensic_data/batch367/issue_337.json",
   "bytes": 4544,
   "sha256": "f595c7732fc9e1def80c34da1bbf086320ae455b91cf70a7e4cc8d6c0ac20867"
  },
  {
   "path": "forensic_data/batch367/issue_337_comments.json",
   "bytes": 2547,
   "sha256": "ef469027958b95feffe52e460cf77eb18fbf8d2b7375c2e657ed5e8cf6ba04d8"
  },
  {
   "path": "forensic_data/batch367/issue_338.json",
   "bytes": 4295,
   "sha256": "2d2c23ca845dabff4b1a41e2016f6f0ad5ae123eb7086b7cb4f8337b6c958b8f"
  },
  {
   "path": "forensic_data/batch367/issue_338_comments.json",
   "bytes": 1986,
   "sha256": "54fa025e0bdd031ad956b980fa78f223d7a204f1d793c32ceb696ec4cceb5b29"
  },
  {
   "path": "forensic_data/batch367/issue_340.json",
   "bytes": 4297,
   "sha256": "0c0e04b117e10f2a365d3dc115f40f5afa4d3f8de6277f4c8a4c16c5f7550d5f"
  },
  {
   "path": "forensic_data/batch367/issue_340_comments.json",
   "bytes": 2019,
   "sha256": "c7c62d373161b390fe509266fa4d9644293bd93ad559c0a86c2d59ce41ce281c"
  },
  {
   "path": "forensic_data/batch367/issue_341.json",
   "bytes": 4397,
   "sha256": "2c55830c9ae50acb2635262ece00947d1227ddef7f6b1305d5851ceed9251867"
  },
  {
   "path": "forensic_data/batch367/issue_341_comments.json",
   "bytes": 2052,
   "sha256": "583a68605c1818a0918b522af2b6e058d9bd7a99c3eed668458d3b4f5e047c23"
  },
  {
   "path": "forensic_data/batch367/issue_342.json",
   "bytes": 7151,
   "sha256": "bb41fb2ef8da868b6b485d0dd1c515157b65597b4534e39793ef8aefd7210e01"
  },
  {
   "path": "forensic_data/batch367/issue_342_comments.json",
   "bytes": 3027,
   "sha256": "82e5466d3169fcfc9f5cf174a3153f84ab31d635821f017bf56b0413279bc709"
  },
  {
   "path": "forensic_data/batch367/issue_345.json",
   "bytes": 6029,
   "sha256": "bcc174c0c1cabbe9fbae773265eb3cb3f062077296e68aff9dfd487806ee2bd8"
  },
  {
   "path": "forensic_data/batch367/issue_345_comments.json",
   "bytes": 3824,
   "sha256": "8b5da55a0c01aee480afe3767a41f8cb96f32280f7a6c14f9ef5e65aedcd933b"
  },
  {
   "path": "forensic_data/batch367/issue_347.json",
   "bytes": 5103,
   "sha256": "81c95830517771d1102b5475977928cbfa8f6fc258bad55b236830dac17989cf"
  },
  {
   "path": "forensic_data/batch367/issue_347_comments.json",
   "bytes": 4241,
   "sha256": "9916a102a8a7d781dc228be0afe60604a0bde60707ade079a21da14cd6deb64c"
  },
  {
   "path": "forensic_data/batch367/issue_349.json",
   "bytes": 5539,
   "sha256": "51443a6fbdae42663d012c4d046797b8f1d8b8c8954d982cee905e5e1edb8994"
  },
  {
   "path": "forensic_data/batch367/issue_349_comments.json",
   "bytes": 4175,
   "sha256": "c67e8fd20b0d54444fa86fff14ba7837080d7c286fd55ac7bb3bd0fc93579d6a"
  },
  {
   "path": "forensic_data/batch367/issue_350.json",
   "bytes": 5803,
   "sha256": "96747f34911c80e2ef171e242078f8251c439b3fb136319eaed1cca83cd2c0ac"
  },
  {
   "path": "forensic_data/batch367/issue_350_comments.json",
   "bytes": 4077,
   "sha256": "0423e56a753c76cc80b7e69267fa7c8db8e78f12bd9e3a79b1461953eca2330c"
  },
  {
   "path": "forensic_data/batch367/issue_352.json",
   "bytes": 4655,
   "sha256": "750c9a53023996a87a95a598d14b352c673f753e1236cefa460bbf992792c5f2"
  },
  {
   "path": "forensic_data/batch367/issue_352_comments.json",
   "bytes": 4837,
   "sha256": "01bebdf39e44d2d9dd45eeb14e5827afc9e602282b28af9dbb09f35291c3f38b"
  },
  {
   "path": "forensic_data/batch367/issue_3_comments.json",
   "bytes": 7079,
   "sha256": "4ccfe4fa9358bf1d91f48cec089b4815d954c3baea89a65ae545593b6aac472f"
  },
  {
   "path": "forensic_data/batch367/issue_4.json",
   "bytes": 11547,
   "sha256": "6d5ec3db8a47fdb5df492e069ed3d94e642d6ba07b02db0ff6769b6171010fe9"
  },
  {
   "path": "forensic_data/batch367/issue_4_comments.json",
   "bytes": 7698,
   "sha256": "93fd417fdc0df14e10fa6ba6cb5d8c303ebba98a714d26c5909a7dc5a53563ea"
  },
  {
   "path": "forensic_data/batch367/issue_5.json",
   "bytes": 10056,
   "sha256": "1b8bafaa85b7dc4f905e1f3bb98217c68a966557a882ff2a99c374186512550a"
  },
  {
   "path": "forensic_data/batch367/issue_5_comments.json",
   "bytes": 7491,
   "sha256": "6d86d3ff0a150253faf3ccdb8ea61035270afe8f4683534f166d674c27cc5936"
  },
  {
   "path": "forensic_data/batch367/issue_6.json",
   "bytes": 10388,
   "sha256": "b0c21377646e258b34e18493daa23d803371a42897d9d616fdbb37c005cd47da"
  },
  {
   "path": "forensic_data/batch367/issue_68.json",
   "bytes": 8079,
   "sha256": "93cb0b9f36f618a7c2cbbfd5e4246bf957c30a6966eb0b2757da8189b08e26bd"
  },
  {
   "path": "forensic_data/batch367/issue_68_comments.json",
   "bytes": 5671,
   "sha256": "85157c190c12439c7dc7fea04273591cc641b92f8b2215c13654465eddf9e841"
  },
  {
   "path": "forensic_data/batch367/issue_6_comments.json",
   "bytes": 7511,
   "sha256": "d874f7357e98bc402025da1f9a2d60bf7842a42259cfb3e8c1d81412178bc3d2"
  },
  {
   "path": "forensic_data/batch367/issue_7.json",
   "bytes": 7170,
   "sha256": "8794256bdd5533df40e5870e20667d9b16d85fa8a619443ba81894d12c1b788f"
  },
  {
   "path": "forensic_data/batch367/issue_7_comments.json",
   "bytes": 47986,
   "sha256": "76561407d9159d9fdecdac0299b0a33ce3e0aad610b5ec3fab2262700f92800e"
  },
  {
   "path": "forensic_data/batch367/issue_8.json",
   "bytes": 6010,
   "sha256": "fd77e00a6a0de7305fc095fecf7e7f6b93f0e5cb5d38fdf77a1e93feb8c7e3fa"
  },
  {
   "path": "forensic_data/batch367/issue_81.json",
   "bytes": 8063,
   "sha256": "ae19fd4273866b0253449bbf6978fe56b584ed563676189411e29ea3a5bf9caa"
  },
  {
   "path": "forensic_data/batch367/issue_81_comments.json",
   "bytes": 5621,
   "sha256": "847c941b5324b597f0ecebec37910595b4e4ce98eb928d0f98a47349fbbe6587"
  },
  {
   "path": "forensic_data/batch367/issue_8_comments.json",
   "bytes": 236434,
   "sha256": "4ac2876e59825f08137e233e51749669ece0d35a1044340feaa125dd23c7d241"
  },
  {
   "path": "forensic_data/batch367/records_final.json",
   "bytes": 239565,
   "sha256": "fa26885f083aca0df91606743a476a30690e4fb0cb7932091d03a27740ff0cf9"
  },
  {
   "path": "forensic_data/commits.json.gz",
   "bytes": 610727,
   "sha256": "4a65fd544a8a3dc24d0ccb4ff683326f0a42d6f4e8345544fef89f2a3a6a935d"
  },
  {
   "path": "forensic_data/issue_364.json",
   "bytes": 487,
   "sha256": "7b665782213d98516832614a6e7eff9c53da85282ec1c4db8961741eb57a2c5a"
  },
  {
   "path": "forensic_data/issue_364_comments.json",
   "bytes": 1237123,
   "sha256": "a4debb1549abd33c3a5fcf1550d3701614af00c132e48266e3e2141ed87671eb"
  },
  {
   "path": "forensic_data/issue_365.json",
   "bytes": 487,
   "sha256": "7b665782213d98516832614a6e7eff9c53da85282ec1c4db8961741eb57a2c5a"
  },
  {
   "path": "forensic_data/issue_365_comments.json",
   "bytes": 17775,
   "sha256": "e5a5bdeb8cbfa540fb83c05442e0185813c62e37009d54c9b7b3332692ae0b62"
  },
  {
   "path": "forensic_data/issue_367.json",
   "bytes": 7530,
   "sha256": "a1dbef87f30b1fd7b8f811095fb8564ea77eb9a7887288bafe7852caf8d53184"
  },
  {
   "path": "forensic_data/issue_367_comments.json",
   "bytes": 2,
   "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  },
  {
   "path": "forensic_data/issue_368.json",
   "bytes": 7524,
   "sha256": "e058f26b30372b1d34b4a7156ade78509d633e273da4044b85827862c088ffef"
  },
  {
   "path": "forensic_data/issue_368_comments.json",
   "bytes": 2,
   "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  },
  {
   "path": "forensic_data/issue_369.json",
   "bytes": 7112,
   "sha256": "d58674369870b96ab1a07078f405b6305b50e7542a6dd12ac40915763cfece4f"
  },
  {
   "path": "forensic_data/issue_369_comments.json",
   "bytes": 2,
   "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  },
  {
   "path": "forensic_data/issues_all.json",
   "bytes": 4908274,
   "sha256": "28dbfaa23d37d7251effcc7abbfa3c1d8a5a390ebf907ccc027aff0f554587fd"
  },
  {
   "path": "forensic_data/ledger_stats.json",
   "bytes": 681,
   "sha256": "c3ffbc87341344f9fbe839321c03a1cf87ad9d21b9cbf9baad3e37d227d72bde"
  },
  {
   "path": "forensic_data/s220_issues.json",
   "bytes": 748505,
   "sha256": "f4d88ba92a14c75b4ab3235a9e21aed0caf756af1568e9c5067c6c8a681d1807"
  }
 ],
 "retrieval": "python3 scripts/forensic_ledger.py fetch (re-downloads issues/comments/commits into ignored .cache/forensics/<snapshot-id>/)",
 "retention_owner": "release engineering (#587 WP2/R27)"
}
```
