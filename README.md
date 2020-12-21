# random_number_game

Standard oTree Version

### Suggested session config:

```
dict(
        name='random_number_game',
        display_name="Random Number Game",
        num_demo_participants=4,
	app_sequence=['random_number_game']
     )
```

update models.py for number of players and rounds to:
```python
num_rounds = 150
```

update pages.py/ProcessingPage/before_next_page for number of players and rounds to:
```python
self.participant.vars['expiry_time'] = time() + 3*60
```

