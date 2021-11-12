# Lunch Money Automation
This repository includes some helpful automation tools to help you keep your Lunch Money
data in order. They run on a scheduled cron job (using GitHub Actions) and take care of
things like grouping transfers between your accounts and linking spare change savings (if
you use them).

If you're like me, these transactions make up 80%+ of your monthly transaction count
and being able to condense them into something vaguely readable is an absolute game
changer.

The automation tasks themselves are written in Python (so they should be easy to code review)
and have a good amount of testing to help ensure they work as intended, but as with all
things you find on the internet: this comes with no guarantees of any kind and you are
responsible for any issues that arise.

## How does it work?
This automation package runs inside GitHub Actions as a scheduled job, making it pretty easy
to set up your own version (just fork this repository, create a `LUNCHMONEY_TOKEN` secret and
tweak the `LUNCHMONEY_CONFIG` in `.github/workflows/run.yml`).

## Tasks
### Link Transactions
This task is responsible for linking any transactions between your accounts. It does so by
looking for transactions that are within a specific category (I use `Transfers`), have
the same amount, a similar-enough date, and whose payees match the format "To `$ACCOUNT`" or
"From `$ACCOUNT`".

In other words, it will link the following transactions together:

| Date | Category | Account | Payee | Amount |
| ---- | -------- | ------- | ----- | ------ |
| 2020-01-01 | Transfers | Savings | To Checking | $100.00 |
| 2020-01-03 | Transfers | Checking | From Savings | $100.00 |

When linking these transactions together, the group will include a note reflecting the amount
of money that was transferred (since Lunch Money will show a sum of $0.00 when you're transferring
between your own accounts). We also generate a compound payee name of the form "$ACCOUNT1 to $ACCOUNT2".

### Link Spare Change
This task is responsible for linking any spare change transactions between your accounts.
Some banks will allow you to round up your transactions to the nearest dollar, and this
will be deposited in a savings account automatically. I have found that grouping these
transactions in Lunch Money with the original purchase makes it far easier to keep track
of and far less "noisy".

The grouping itself will look for transactions from a main account to a savings account
which have a corresponding transaction whose sum rounds to the nearest dollar. It will
link these together into a single group (including both sides of the transfer, if present).

In other words, it will link the following transactions together:

| Date | Category | Account | Payee | Amount |
| ---- | -------- | ------- | ----- | ------ |
| 2020-01-01 | Purchases | Checking | Coffee | $3.47 |
| 2020-01-01 | Transfers | Checking | To Savings | $0.53 |
| 2020-01-01 | Transfers | Savings | From Checking | $0.53 |

When linking these transactions together, the group will reflect the cost of the original
purchase since the transfers will cancel one another out (you're not losing money here, just
shifting it to a savings account). The group's payee name will reflect the original purchase's
payee.
