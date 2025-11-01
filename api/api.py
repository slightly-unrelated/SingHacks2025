from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, sys, uvicorn
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from doc_processing import pdf_pro, img_pro, text_pro
from uuid import uuid4
import json, cv2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/process/pdf")
async def process_pdf(file: UploadFile):
    try:
        uid = str(uuid4())
        out_dir = os.path.join("doc_processing", "output_images", uid)
        os.makedirs(out_dir, exist_ok=True)
        pdf_path = os.path.join(out_dir, file.filename)
        with open(pdf_path, "wb") as f: f.write(await file.read())
        pages = pdf_pro.pdf_to_png(pdf_path, out_dir)
        items = []
        for i, p in enumerate(pages):
            j = os.path.join(out_dir, f"page_{i}.json")
            img = cv2.imread(p)
            img_pro.ocr_to_json(img, j)
            with open(j, "r", encoding="utf-8") as jf: items += json.load(jf)
        combined = os.path.join(out_dir, "combined.json")
        with open(combined, "w", encoding="utf-8") as cf: json.dump(items, cf, ensure_ascii=False, indent=2)
        rep_path = os.path.join(out_dir, "report.json")
        rep = text_pro.analyze(combined, out=rep_path)
        return {"id": uid, "pages": len(pages), "report": json.loads(rep), "artifacts": {"dir": out_dir, "pdf": pdf_path, "combined": combined, "report": rep_path}}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/process/image")
async def process_image(file: UploadFile):
    
    try:
        uid = str(uuid4())
        out_dir = os.path.join("doc_processing", "output_images", uid)
        os.makedirs(out_dir, exist_ok=True)
        img_path = os.path.join(out_dir, file.filename)
        with open(img_path, "wb") as f: f.write(await file.read())
        img = cv2.imread(img_path)
        j = os.path.join(out_dir, "ocr.json")
        img_pro.ocr_to_json(img, j)
        rep_path = os.path.join(out_dir, "report.json")
        rep = text_pro.analyze(j, out=rep_path)
        return {"id": uid, "report": json.loads(rep), "artifacts": {"dir": out_dir, "image": img_path, "ocr": j, "report": rep_path}}
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
    
