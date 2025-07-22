def _load_flows(self):
        """
        flows.json에서 flow 데이터 로드

        flows.json 구조:
        {
            "flows": [...],
            "current_flow_id": "...",
            "last_saved": "...",
            "version": "2.0"
        }
        """
        flows_path = os.path.join(self.data_dir, 'flows.json')

        if os.path.exists(flows_path):
            try:
                with open(flows_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.flows = data.get('flows', [])

                    # current_flow_id가 있으면 해당 flow 찾기
                    current_id = data.get('current_flow_id')
                    if current_id:
                        for flow in self.flows:
                            if flow['id'] == current_id:
                                self.current_flow = flow
                                break

                    # Debug 로그 (debug 속성 확인)
                    if hasattr(self, 'debug') and self.debug:
                        print(f"✅ Flow 데이터 로드 완료: {len(self.flows)}개 flow")

            except Exception as e:
                if hasattr(self, 'debug') and self.debug:
                    print(f'❌ Flow 데이터 로드 실패: {e}')
                self.flows = []
        else:
            # flows.json이 없으면 빈 리스트로 초기화
            self.flows = []
            if hasattr(self, 'debug') and self.debug:
                print("📝 flows.json 파일이 없습니다. 새로 생성됩니다.")

