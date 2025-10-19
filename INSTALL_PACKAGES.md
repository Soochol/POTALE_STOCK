# 패키지 설치 가이드

비동기 수집 시스템을 사용하기 위해 추가 패키지를 설치해야 합니다.

## 방법 1: pip 사용 (권장)

```bash
cd c:\myCode\potale_stock
pip install aiohttp aiofiles aiodns
```

## 방법 2: requirements.txt 일괄 설치

```bash
cd c:\myCode\potale_stock
pip install -r requirements.txt
```

## 방법 3: uv 사용 (빠름)

```bash
cd c:\myCode\potale_stock
uv pip install aiohttp aiofiles aiodns
```

## 설치 확인

설치 후 다음 명령으로 확인:

```bash
python test_async_import.py
```

정상 설치 시 다음과 같은 출력:

```
테스트 시작...
1. database/queries.py 임포트 테스트...
   ✓ 성공
2. incremental_collector.py 임포트 테스트...
   ✓ 성공
3. async_naver_hybrid_collector.py 임포트 테스트...
   ✓ 성공
4. async_bulk_collector.py 임포트 테스트...
   ✓ 성공

모든 테스트 통과! ✓
```

## 문제 해결

### ImportError: No module named 'aiohttp'
→ 패키지 설치 필요: `pip install aiohttp aiofiles aiodns`

### No module named 'pip'
→ Python 재설치 또는 get-pip.py 다운로드

### externally-managed-environment
→ 가상환경 사용: `python -m venv venv` → `venv\Scripts\activate`
