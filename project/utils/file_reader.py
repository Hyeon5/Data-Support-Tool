"""파일 읽기 유틸리티.

xlsx / xls / csv 파일을 pandas DataFrame 으로 읽는다.
모든 값을 원본 그대로 유지하기 위해 자동 형 변환을 최소화한다.
"""

from __future__ import annotations

import os

import pandas as pd

from ..config import Settings


class FileReadError(Exception):
    """파일 읽기 실패 시 발생하는 예외."""


class FileReader:
    """지원 형식의 데이터 파일을 DataFrame 으로 읽는 클래스."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def read(self, file_path: str) -> pd.DataFrame:
        """파일을 읽어 DataFrame 을 반환한다.

        Args:
            file_path: 읽을 파일 경로.

        Returns:
            원본 데이터를 담은 DataFrame.

        Raises:
            FileReadError: 파일이 없거나, 지원하지 않는 형식이거나,
                읽기에 실패한 경우.
        """
        if not file_path:
            raise FileReadError("파일 경로가 비어 있습니다.")
        if not os.path.exists(file_path):
            raise FileReadError(f"파일을 찾을 수 없습니다: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self._settings.SUPPORTED_EXTENSIONS:
            raise FileReadError(
                f"지원하지 않는 파일 형식입니다: {ext} "
                f"(지원: {', '.join(self._settings.SUPPORTED_EXTENSIONS)})"
            )

        try:
            if ext == ".csv":
                df = self._read_csv(file_path)
            elif ext == ".xls":
                df = pd.read_excel(file_path, engine="xlrd")
            else:  # .xlsx
                df = pd.read_excel(file_path, engine="openpyxl")
        except ImportError as exc:  # 엔진 미설치 등
            raise FileReadError(
                f"파일을 읽는 데 필요한 라이브러리가 없습니다: {exc}"
            ) from exc
        except Exception as exc:  # noqa: BLE001 - 사용자에게 원인 전달
            raise FileReadError(f"파일 읽기에 실패했습니다: {exc}") from exc

        if df is None or df.shape[1] == 0:
            raise FileReadError("데이터가 비어 있거나 컬럼이 없습니다.")

        # 원본 인덱스를 0-based 위치 인덱스로 재설정하여 행 위치를 명확히 한다.
        df = df.reset_index(drop=True)
        return df

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """CSV 를 여러 인코딩으로 시도하며 읽는다(내부망 환경 대응)."""
        encodings = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1")
        last_error: Exception | None = None
        for enc in encodings:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
        # 모든 인코딩 실패 시 마지막 오류를 전달
        raise FileReadError(
            f"CSV 인코딩을 인식하지 못했습니다. (시도: {', '.join(encodings)})"
        ) from last_error
