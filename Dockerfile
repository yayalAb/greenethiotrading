FROM odoo:18.0

USER root

# tesseract-ocr: OCR engine required by pytesseract
# poppler-utils: provides pdftoppm/pdftocairo required by pdf2image
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# opencv-python-headless is used instead of opencv-python: the full build
# requires libGL.so.1 (Mesa/GUI libs) which isn't present in this base image,
# and none of the OCR preprocessing code uses any GUI features.
RUN pip install --ignore-installed --no-cache-dir --break-system-packages \
    pandas num2words abyssinica email-validator pytesseract opencv-python-headless Pillow numpy pdf2image pydantic PyJWT

USER odoo
