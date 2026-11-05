# Release build of the linux-x64-gnu addon on node:22-trixie (Debian 13, glibc 2.41).
# scripts/pack.sh records the highest GLIBC symbol version the .node file needs.
FROM node:22-trixie AS build
ARG RUST_VERSION=1.99.0
ARG PDFUST_GIT_SHA=unknown
ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo PATH=/usr/local/cargo/bin:$PATH \
    PDFUST_GIT_SHA=$PDFUST_GIT_SHA CARGO_TERM_COLOR=never
RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain ${RUST_VERSION}
WORKDIR /src
COPY rust ./rust
COPY bindings/node ./bindings/node
WORKDIR /src/bindings/node
RUN npm ci --no-audit --no-fund
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/bindings/node/target \
    npx napi build --platform --release --js native.js --dts native.d.ts \
    && cp pdfust-node.linux-x64-gnu.node /out.node
RUN objdump -T /out.node | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1 > /glibc-max.txt

FROM scratch AS artifact
COPY --from=build /out.node /pdfust-node.linux-x64-gnu.node
COPY --from=build /src/bindings/node/native.js /native.js
COPY --from=build /src/bindings/node/native.d.ts /native.d.ts
COPY --from=build /glibc-max.txt /glibc-max.txt
