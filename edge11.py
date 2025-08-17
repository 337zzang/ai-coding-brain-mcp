class 한글클래스:
    def 처리함수(self, 데이터, 옵션=None):
        if 옵션:
            결과 = f"특별처리: {데이터} (옵션: {옵션})"
        else:
            결과 = f"기본처리: {데이터}"
        print(f"로그: {결과}")
        return 결과