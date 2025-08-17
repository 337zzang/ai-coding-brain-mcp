class MixedIndent:
	def __init__(self):  # 탭 사용
		self.data = []

    def add_item(self, item):  # 4칸 공백 사용
        self.data.append(item)
        return item

	def get_count(self):  # 탭 사용
		return len(self.data)