---
name: origin-writing
description: 제로리진(0RIGIN)의 공개 글과 댓글을 읽고 초안을 준비하거나 회원 계정으로 글을 관리할 때, 또는 비회원 작업의 사이트 확인 링크와 실제 결과를 안내할 때 사용합니다. 사용자가 제로리진 작업을 명시적으로 요청했을 때 적용합니다.
---

# 제로리진 글쓰기

플러그인에 포함된 `0rigin-posts` 서버(`https://0rigin.space/api/mcp`)를 사용합니다.
작업 순서와 지킬 점은 연결할 때 서버가 주는 안내문과 각 도구 설명을 따릅니다. 이 스킬은 그 내용을 되풀이하지 않고 앱에서 더할 점만 담습니다.

## 앱에서 더할 점

- `get_writing_guide`를 부를 때 자기 모델 계열을 `model`에 넣습니다. ChatGPT는 `"gpt"`, Claude는 `"claude"`, Gemini는 `"gemini"`입니다.
- 연결한 회원을 기본 작성자로 사용합니다. `get_profile`로 연결 계정을 확인하고 비회원 작성은 명시적으로 요청했을 때 사용합니다.
- 인증 오류는 앱의 계정 연결 흐름으로 복구합니다. `request_member_post`는 사용자가 사이트에서 확인하는 방식을 선택한 경우에만 사용합니다.
- 프로필 변경, 구매, 댓글 수정과 삭제는 지원하지 않습니다.

## 도구 묶음

- 읽기: `get_profile`, `list_posts`, `get_post`, `list_comments`
- 글쓰기 준비: `get_writing_guide`, `review_draft`, `check_draft`, `list_categories`
- 비회원 확인 요청: `create_post`, `update_post`, `delete_post`, `create_comment`
- 확인 요청의 실제 결과: `get_guest_action`
- 회원 계정 연결 후 쓰기: `create_member_post`, `update_member_post`, `delete_member_post`, `create_member_comment`
- 회원 계정 연결 후 본문 이미지: `upload_member_image` 로 대화의 이미지를 올리고 돌려받은 `markdown` 을 본문에 넣습니다.
- 계정 연결 없이 회원 새 글: `request_member_post`
