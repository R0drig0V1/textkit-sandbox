<!-- ADR: the e-mail address syntax that textkit.emails.is_email accepts (plan task T3.5). -->
# 0001: What `is_email` accepts

## Context

`is_email(text) -> bool` (plan task T3.5, `textkit/emails.py`) checks an address offline: no
network and no DNS. The full grammar of RFC 5321/5322 allows quoted local parts
(`"a b"@c.co`), comments, address literals (`a@[1.2.3.4]`) and, with RFC 6531, non-ASCII
characters. Almost nothing that sends or stores mail accepts all of that, and a helper that
says "valid" for addresses most systems reject is less useful than a strict one. The
function is also called by the CLI with any string, so it must answer `True`/`False` for
every `str` and never raise for one.

## Decision

`is_email` accepts exactly the addresses that satisfy all of these rules, and returns `False`
for every other `str`:

1. **One `@`.** The text contains exactly one `@`, splitting it into a local part and a
   domain. Since quoted local parts are not accepted (rule 3), an `@` can never be part of
   the local part, so this split is unambiguous.
2. **ASCII only.** Every character is ASCII; non-ASCII letters (`ü`), non-ASCII digits and
   look-alikes such as the Kelvin sign are rejected. Internationalized addresses
   (RFC 6531) and IDN domains in Unicode form are out of scope; punycode domains
   (`xn--...`) pass as ordinary labels. Character classes are written as explicit ASCII
   ranges, never `\w`, `str.isalnum` or `re.IGNORECASE`.
3. **Local part: a dot-atom.** One or more atoms of RFC 5322 `atext` (ASCII letters, digits
   and `` !#$%&'*+/=?^_`{|}~- ``) separated by single dots. So no leading dot, no trailing
   dot, no two dots in a row. Quoted local parts (`"a b"@c.co`) are rejected, as are
   comments and any whitespace.
4. **Domain: a dotted host name.** At least two labels separated by single dots (`a@b` is
   rejected: dotless domains are not deliverable on the public Internet, RFC 7085). Each
   label is 1 to 63 ASCII letters, digits or hyphens and does not start or end with a
   hyphen. No trailing dot (`a@b.co.` is rejected). Address literals (`a@[1.2.3.4]`) are
   rejected. The last label must not be all digits, so a bare IPv4 address (`a@1.2.3.4`)
   is rejected too (RFC 3696 section 2). There is no list of top-level domains: `a@b.c` is
   accepted.
5. **Length limits.** The local part is at most 64 characters (RFC 5321 section 4.5.3.1.1).
   The whole address is at most 254 characters: the 256-octet forward-path of RFC 5321
   minus its angle brackets (RFC 3696 errata 1690). The domain's own 255-octet limit is
   therefore never the binding one. Since everything is ASCII, characters and octets are
   the same count.
6. **No normalization.** Case is kept and accepted as given in both parts; nothing is
   stripped, so leading or trailing whitespace, a trailing newline included, makes the text
   invalid (the implementation uses `re.fullmatch`, not `$`).
7. **Types.** A non-`str` argument raises `TypeError`; a `str` never raises.

## Consequences

- Some RFC-valid addresses are rejected (quoted local parts, address literals, dotless
  domains, internationalized addresses). Callers that need them must use another check.
- Some addresses that pass do not exist or cannot receive mail: syntax is all that is
  checked, by design (no network, no DNS).
- Widening the rules later (for example accepting RFC 6531 addresses) changes results for
  existing callers and needs a new ADR that supersedes this one.

## Cases

Inputs are Python literals; `tests/test_emails.py` tests every row.

| Input | Output | Why |
|-------|--------|-----|
| `"a@b.co"` | `True` | minimal address |
| `"a.b@c.co"` | `True` | dot between atoms |
| `"a+tag@b.co"` | `True` | `+` is atext |
| `"A@B.CO"` | `True` | case is kept and accepted |
| `"a@b-c.co"` | `True` | hyphen inside a label |
| `"a@b.c"` | `True` | no top-level-domain list |
| `".a@b.co"` | `False` | leading dot in the local part |
| `"a.@b.co"` | `False` | trailing dot in the local part |
| `"a..b@c.co"` | `False` | two dots in a row |
| `"a@b"` | `False` | dotless domain |
| `"a@b.co."` | `False` | trailing dot in the domain |
| `"a@.b.co"` | `False` | empty first label |
| `"a@b..co"` | `False` | empty label |
| `"a@-b.co"` | `False` | label starts with a hyphen |
| `"a@b-.co"` | `False` | label ends with a hyphen |
| `"a@1.2.3.4"` | `False` | all-digit last label (bare IPv4) |
| `'"a b"@c.co'` | `False` | quoted local part |
| `"a@[1.2.3.4]"` | `False` | address literal |
| `"ü@b.co"` | `False` | non-ASCII character |
| `"a@b@c.co"` | `False` | two `@` |
| `"@b.co"` | `False` | empty local part |
| `"a@"` | `False` | empty domain |
| `"a"` | `False` | no `@` |
| `" a@b.co"` | `False` | leading space |
| `"a@b.co\n"` | `False` | trailing newline |
| `""` | `False` | empty text |
| `"a"*64 + "@b.co"` | `True` | local part of 64 characters (the limit) |
| `"a"*65 + "@b.co"` | `False` | local part of 65 characters |
| `"a@" + "b"*63 + ".co"` | `True` | label of 63 characters (the limit) |
| `"a@" + "b"*64 + ".co"` | `False` | label of 64 characters |
| `"a@" + ".".join(["b"*63]*3) + "." + "c"*60` | `True` | 254 characters (2 + 3*63 + 3 dots + 60), every label at most 63 |
| `"a@" + ".".join(["b"*63]*3) + "." + "c"*61` | `False` | 255 characters (2 + 3*63 + 3 dots + 61), every label at most 63 |
