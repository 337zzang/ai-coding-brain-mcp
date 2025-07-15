# 상수 정의
ADULT_AGE = 18
PREMIUM_DISCOUNT = 0.2
STANDARD_DISCOUNT = 0.1

def is_eligible_user(user):
    """사용자가 할인 대상인지 확인"""
    return (user.get('age', 0) > ADULT_AGE and 
            user.get('status') == 'active')

def get_user_discount(user):
    """사용자의 할인율 계산"""
    if user.get('subscription') == 'premium':
        return PREMIUM_DISCOUNT
    return STANDARD_DISCOUNT

def create_user_record(user, discount):
    """사용자 레코드 생성"""
    return {
        'name': user.get('name'),
        'email': user.get('email'),
        'discount': discount
    }

def process_user_data(users):
    """활성 성인 사용자들의 할인 정보 처리"""
    result = []

    for user in users:
        if not is_eligible_user(user):
            continue

        discount = get_user_discount(user)
        record = create_user_record(user, discount)
        result.append(record)

    return result

def calculate_total(items):
    """할인이 적용된 총액 계산"""
    return sum(
        item.get('price', 0) * (1 - item.get('discount', 0))
        for item in items
    )
