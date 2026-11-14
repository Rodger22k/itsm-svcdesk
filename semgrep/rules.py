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
    # ruleid: svcdesk-direct-request-json
    return await request.json()


async def parse_prevalidated_request(parser):
    # ok: svcdesk-direct-request-json
    return await parser.parse_json()


def parse_request_synchronously(request):
    # ok: svcdesk-direct-request-json
    return request.json()
