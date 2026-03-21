#!/bin/bash
# Dynamically find and register the OpenXR XCR capture layer from the
# installed isaaclab/isaacsim package.

XCR_JSON=$(find /workspace/sim-vr/.venv -path "*/bin/openxr_xcr_capture_layer.json" 2>/dev/null | head -1)
if [ -z "$XCR_JSON" ]; then
    echo "[fix_xcr_layer] XCR capture layer JSON not found -- skipping"
    exit 0
fi

XCR_DIR=$(dirname "$XCR_JSON")
XCR_SO="$XCR_DIR/libxcr-capture-oxr-layer.so"

if [ ! -f "$XCR_SO" ]; then
    echo "[fix_xcr_layer] libxcr-capture-oxr-layer.so not found at $XCR_DIR -- skipping"
    exit 0
fi

# Write the layer JSON with an absolute path to the .so
cat > /usr/share/openxr/1/api_layers/implicit.d/openxr_xcr_capture_layer.json <<EOF
{
    "file_format_version": "1.0.0",
    "api_layer": {
        "name": "XR_APILAYER_NVIDIA_xcr_capture",
        "library_path": "$XCR_SO",
        "api_version": "1.0",
        "implementation_version": "1",
        "description": "API layer to capture data from OXR app to file",
        "disable_environment": "DISABLE_XR_API_LAYER_XCR_CAPTURE",
        "instance_extensions": [
            {
                "name": "XR_NVX1_xcr_capture_interaction",
                "extension_version": "1"
            }
        ]
    }
}
EOF

echo "[fix_xcr_layer] Registered XCR capture layer: $XCR_SO"
