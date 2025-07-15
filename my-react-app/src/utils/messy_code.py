def process_user_data(users):
    result = []
    for i in range(len(users)):
        if users[i]['age'] > 18:
            if users[i]['status'] == 'active':
                if users[i]['subscription'] == 'premium':
                    temp = {}
                    temp['name'] = users[i]['name']
                    temp['email'] = users[i]['email']
                    temp['discount'] = 0.2
                    result.append(temp)
                else:
                    temp = {}
                    temp['name'] = users[i]['name']
                    temp['email'] = users[i]['email']
                    temp['discount'] = 0.1
                    result.append(temp)
    return result

def calculate_total(items):
    total = 0
    for i in range(len(items)):
        total = total + items[i]['price'] * (1 - items[i]['discount'])
    return total
