import cv2
import json
import os
import pytesseract
import math
if os.name == "nt":
	tpath = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
	if os.path.exists(tpath):
		pytesseract.pytesseract.tesseract_cmd = tpath


def auto_orient(img):
	try:
		ang = 0
		for ln in pytesseract.image_to_osd(img).splitlines():
			if ln.startswith("Rotate:"):
				ang = int(ln.split(":",1)[1])
				break
		return (
			cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE) if ang == 90 else
			cv2.rotate(img, cv2.ROTATE_180) if ang == 180 else
			cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) if ang == 270 else img
		)
	except Exception:
		return img

def deskew(img):
	try:
		g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
		bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
		ed = cv2.Canny(bw, 50, 150)
		ln = cv2.HoughLinesP(ed, 1, math.pi/180, 100, minLineLength=min(img.shape[:2])//3, maxLineGap=20)
		if ln is None: return img
		A=[]
		for x1,y1,x2,y2 in ln[:,0]:
			a = math.degrees(math.atan2(y2-y1, x2-x1))
			if -45 < a < 45: A.append(a)
		if not A: return img
		A.sort(); n=len(A); ang = (A[n//2] if n%2 else (A[n//2-1]+A[n//2])/2)
		if abs(ang) < 0.3: return img
		h,w = img.shape[:2]
		M = cv2.getRotationMatrix2D((w/2, h/2), ang, 1.0)
		return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
	except Exception:
		return img

def clean_scan(path, output=None):
	img = deskew(auto_orient(cv2.imread(path)))
	bw = cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
	if output:
		cv2.imwrite(output, bw)
		return output
	return bw



def ocr_to_json(path, output_json, lang="eng", psm=3):
	img = deskew(auto_orient(cv2.imread(path)))
	data = pytesseract.image_to_data(img, lang=lang, config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
	items = []
	for i, text in enumerate(data["text"]):
		t = text.strip()
		if not t:
			continue
		items.append({
			"text": t,
			"conf": float(data["conf"][i]),
			"left": int(data["left"][i]),
			"top": int(data["top"][i]),
			"width": int(data["width"][i]),
			"height": int(data["height"][i])
		})
	with open(output_json, "w", encoding="utf-8") as f:
		json.dump(items, f, ensure_ascii=False, indent=2)
	return output_json


clean_scan("doc_processing/output_images/test_p0.png", "doc_processing/output_images/test_p0_cleaned.png")
ocr_to_json("doc_processing/output_images/test_p0.png", "doc_processing/output_images/test_p0_ocr.json")