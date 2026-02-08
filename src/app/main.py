from fastapi import FastAPI

app = FastAPI(title="Course Registration API")


@app.get("/health")
def health():
    return {"status": "ok"}
