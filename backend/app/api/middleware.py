"""Bound request bodies before multipart parsing/spooling."""
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app, limit: int):
        self.app = app
        self.limit = limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        content = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(content) + len(chunk) > self.limit:
                response = JSONResponse({"detail": "Request vượt giới hạn dung lượng cho phép."}, status_code=413)
                await response(scope, receive, send)
                return
            content.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(content), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
