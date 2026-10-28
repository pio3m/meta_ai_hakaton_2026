class Quest:
    def __init__(self, data):
        self.data = data
        self.index = 0
        self.inventory = set()
        self.reward_count = 0

    @property
    def complete(self):
        return self.index == len(self.data['steps'])

    @property
    def current(self):
        return None if self.complete else self.data['steps'][self.index]

    @property
    def objective(self):
        return self.data['completion_message'] if self.complete else self.current['objective']

    def interact(self, target):
        step = self.current
        if step is None or step['target'] != target:
            return None
        item = step.get('grant_item')
        if item and item not in self.inventory:
            self.inventory.add(item)
            self.reward_count += 1
        self.index += 1
        return step['id']
