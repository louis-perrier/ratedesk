# ratedesk

A hotel back office where the rate form changes shape depending on who fills it in.

A revenue manager sees every property and prices freely. A distribution partner
only sees the rates of his own channel, on the hotels he has a contract on, and
that contract sets him a price floor, a discount cap and a minimum stay. Errors
appear while he types, without going through the save button.

> Built to demonstrate one specific Django admin mechanism, not to run a hotel.
> The scope is deliberately narrow, the code is complete and tested.

## The idea

The contract rules live in a single file, `rates/rules.py`, which knows nothing
about the admin or about forms. The form calls them on save, and a check route
calls them while the row is typed. No rule is written twice, so the two paths
cannot drift apart. A test compares both messages character for character.

A partner's channel is never read from the browser. It comes from the session,
which makes the check route exactly as safe as the form itself.

## Running it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver
```

Then `http://127.0.0.1:8000/admin/`. Three accounts, password `demo`:

| Account | What it sees |
| --- | --- |
| `manager` | everything, bound by no contract |
| `booking` | its rates on both hotels |
| `expedia` | its rates on one hotel only, it has no contract on the other |

## What it demonstrates

**The form changes with the group.** Fields, read only fields and the queryset
behind the channel selector are decided per request, from the connected user.

**Defaults come from the contract.** A new rate line opens on the floor price,
the minimum stay and the cancellation notice of that partner's contract, not on
a constant.

**Errors show up during typing.** A route replays the same Django form and
returns its errors as JSON. The script only displays them, it validates nothing.

**The browser is not what protects the data.** The channel field is `disabled`,
so Django uses the value the server set and ignores what was posted. Forging a
request changes nothing.

## Tests

```bash
.venv/bin/python manage.py test rates
```

31 tests, including the ones that forge a request to prove the last point above.
