import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("啟動普元後端 API 服務器")
    print("=" * 60)
    print("訪問 API 文檔: http://0.0.0.0:8000/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
