def _save_flows(self, force: bool = False) -> bool:
        """
        Flow 데이터 저장 (개선된 버전)

        Args:
            force: 강제 저장 여부

        Returns:
            bool: 저장 성공 여부
        """
        flows_path = os.path.join(self.data_dir, 'flows.json')

        try:
            # 저장할 데이터 준비
            save_data = {
                'flows': self.flows,
                'current_flow_id': self.current_flow['id'] if self.current_flow else None,
                'last_saved': datetime.now().isoformat(),
                'version': '2.0'
            }

            # 임시 파일에 먼저 저장
            temp_path = flows_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # 원자적 이동
            shutil.move(temp_path, flows_path)

            # 로깅
            if hasattr(self, '_last_save_time'):
                elapsed = (datetime.now() - self._last_save_time).total_seconds()
                if elapsed > 60:
                    print(f"💾 Flows 자동 저장 ({len(self.flows)} flows)")

            self._last_save_time = datetime.now()
            self._save_error_count = 0
            return True

        except Exception as e:
            if not hasattr(self, '_save_error_count'):
                self._save_error_count = 0
            self._save_error_count += 1

            if self._save_error_count <= 3:
                print(f"⚠️ Flow 저장 실패 ({self._save_error_count}회): {e}")

            return False
# 클래스 종료
