class MixedIndent:
	def __init__(self):
		self.data = []

    def add_item(self, item):  # 공백 4칸
        self.data.append(item)
        return item