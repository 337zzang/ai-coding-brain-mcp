
    def _add_event(self, event_type: str, entity_id: str, data: Dict):
        """이벤트 추가 및 메시지 발행"""
        event = {
            "type": event_type,
            "entity_id": entity_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # 이벤트를 별도 파일에 저장
        try:
            # 기존 이벤트 로드
            events_data = []
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # 리스트/딕셔너리 모두 처리 가능하도록
                    if isinstance(loaded_data, list):
                        events_data = loaded_data
                    elif isinstance(loaded_data, dict) and "events" in loaded_data:
                        events_data = loaded_data["events"]
                    else:
                        print(f"⚠️ 예상치 못한 이벤트 파일 구조: {type(loaded_data)}")
                        events_data = []

            events_data.append(event)

            # 이벤트가 너무 많으면 오래된 것 제거 (최대 1000개)
            if len(events_data) > 1000:
                events_data = events_data[-1000:]

            # 파일에 저장 (리스트 형태로 통일)
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"이벤트 저장 오류: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # MessageController를 통해 AI용 메시지 발행
        self.msg_controller.emit(event_type, entity_id, data)
