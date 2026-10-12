#!/usr/bin/env bash
# Regenerate assets/encrypted/matrix/*.pdf (CC0, generated). Needs qpdf and PyMuPDF.
#   mu-*  MuPDF: /Encrypt inline in the trailer or xref stream (classic and xref-stream).
#   q-*   qpdf: indirect /Encrypt; RC4-40/128, AES-128, AES-256 R5/R6, clear/encrypted
#         metadata, classic xref vs object streams (xref stream). Passwords: user "userpw"
#         (or empty), owner "ownerpw".
# Usage: generate_matrix.sh <plain.pdf> <out-dir>
set -euo pipefail
plain=$1 out=$2
python3 - "$out" <<'PY'
import sys, fitz
out = sys.argv[1]
doc = fitz.open()
for i in range(2):
    doc.new_page().insert_text((72, 100), f"Encrypted matrix page {i + 1} quick brown fox", fontsize=14)
algs = {"rc4-40": fitz.PDF_ENCRYPT_RC4_40, "rc4-128": fitz.PDF_ENCRYPT_RC4_128,
        "aes-128": fitz.PDF_ENCRYPT_AES_128, "aes-256": fitz.PDF_ENCRYPT_AES_256}
for name, alg in algs.items():
    for pw in ("", "userpw"):
        for xrefstm in (0, 1):
            kw = dict(encryption=alg, owner_pw="ownerpw", user_pw=pw)
            if xrefstm:
                kw["use_objstms"] = 1
            data = doc.tobytes(**kw)
            open(f"{out}/mu-{name}-{'user' if pw else 'empty'}-{'xrefstm' if xrefstm else 'classic'}.pdf", "wb").write(data)
PY
for pw in "" userpw; do tag=$([ -z "$pw" ] && echo empty || echo user)
  for md in clear enc; do for os in classic objstm; do
    mdopt=""; [ $md = clear ] && mdopt="--cleartext-metadata"
    osopt="--object-streams=disable"; [ $os = objstm ] && osopt="--object-streams=generate"
    qpdf --allow-weak-crypto $osopt --encrypt "$pw" ownerpw 40 $mdopt -- "$plain" "$out/q-rc4-40-$tag-$md-$os.pdf"
    qpdf --allow-weak-crypto $osopt --encrypt "$pw" ownerpw 128 --use-aes=n $mdopt -- "$plain" "$out/q-rc4-128-$tag-$md-$os.pdf"
    qpdf $osopt --encrypt "$pw" ownerpw 128 --use-aes=y $mdopt -- "$plain" "$out/q-aes-128-$tag-$md-$os.pdf"
    qpdf $osopt --encrypt "$pw" ownerpw 256 $mdopt -- "$plain" "$out/q-aes-256-r6-$tag-$md-$os.pdf"
    qpdf $osopt --encrypt "$pw" ownerpw 256 --force-R5 $mdopt -- "$plain" "$out/q-aes-256-r5-$tag-$md-$os.pdf"
  done; done
done
