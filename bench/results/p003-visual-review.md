
A bounded authored DEV source audit now separates literal recovery from physical
structure. Haiku640 r912 adds an unsupported wholly empty fifth column;
r51d adds an unsupported blank Amount subcolumn under a two-column header;
r838 loses a visibly present two-row Description merge. All three retain content
precision/recall 1, which does not certify span membership. Actual source pixels,
frozen gold matrices, actual output matrices and zero-based span witnesses are
retained under ignored `visual-review-v1/random40-span-aa74d7f579e3efb6c76a/`.
Original strict scores, references and existing images remain unchanged. Future
lexical partition captions reject wholly empty added columns and require source
review for physical boundary ambiguity. This corrects the older r912 diagnostic's
overbroad accepted-granularity caption without changing that frozen image.
