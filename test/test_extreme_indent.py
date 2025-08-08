class ExtremeNesting:
    def complex_method(self, data):
        """극한의 중첩 테스트"""
        if data:
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if value > 0:
                            try:
                                result = value * 2
                                if result > 100:
                                    while result > 50:
                                        result = result // 2
                                        if result < 75:
                                            with open("test.txt", "w") as f:
                                                f.write(str(result))
                                                for i in range(3):
                                                    if i > 0:
                                                        # 최대 깊이!
                                                        print(f"Deep: {i}")
                            except Exception as e:
                                print(e)
