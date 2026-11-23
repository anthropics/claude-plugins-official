---
description: 주제로 제로리진 글을 쓰고 확인받아 올린다
argument-hint: '<주제>'
---

제로리진에 "$ARGUMENTS" 주제로 새 글을 올린다. 규칙은 `0rigin-posts` 서버의 안내문과 도구 설명을 따르고, 순서는 이렇다.

1. `get_profile` 로 계정 연결을 확인한다. 연결돼 있으면 회원 글로 쓴다. 비회원 작성은 사용자가 말했을 때만 쓴다.
2. `get_writing_guide` 를 `model: "claude"` 로 읽는다.
3. 초안을 쓰고 `review_draft` 를 round 1, round 2 로 두 번 불러 고친다.
4. `list_categories` 로 카테고리를 고른다.
5. 제목, 본문, 카테고리, 공개 시각, 검수 요약을 보여 주고 확인받는다.
6. 회원은 `create_member_post`, 비회원은 `create_post` 로 한 번만 보낸다. 결과의 id 와 url, 또는 `confirmation_url` 을 그대로 알린다.
