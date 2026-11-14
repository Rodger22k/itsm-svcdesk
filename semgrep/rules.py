# ai-generated: 90% - OpenAI Codex drafted true and false cases for the two svcdesk-specific Semgrep rules; the student ran semgrep --test


class FakeStore:
    def create(self, ticket):
        return ticket


store = FakeStore()


async def create_ticket(ticket):
    # ruleid: svcdesk-sync-store-call-in-async
    store.create(ticket)
    return ticket


def import_ticket_in_batch(ticket):
    # ok: svcdesk-sync-store-call-in-async
    store.create(ticket)
    return ticket


async def create_ticket_with_async_repository(repository, ticket):
    # ok: svcdesk-sync-store-call-in-async
    await repository.create(ticket)
    return ticket


async def parse_request(request):
    # ruleid: svcdesk-broad-exception-in-async
    try:
        return await request.json()
    except Exception as error:
        raise ValueError("invalid request") from error


def parse_request_synchronously(request):
    # ok: svcdesk-broad-exception-in-async
    try:
        return request.json()
    except Exception as error:
        raise ValueError("invalid request") from error


async def parse_expected_validation_error(request):
    # ok: svcdesk-broad-exception-in-async
    try:
        return await request.json()
    except ValueError as error:
        raise ValueError("invalid request") from error
