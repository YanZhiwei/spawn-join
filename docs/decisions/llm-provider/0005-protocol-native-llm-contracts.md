# ADR-0005: 閲囩敤鍗忚鍘熺敓 LLM 濂戠害涓庣嫭绔嬫笭閬撹竟鐣?
- Status: Proposed
- Date: 2026-10-29
- Domain: llm-provider
- Classification: 绾︽潫 LLM 棰嗗煙濂戠害銆佸崗璁€傞厤鍜屾笭閬撹竟鐣岋紝灞炰簬 LLM 棰嗗煙鐨勮法妯″潡鏋舵瀯鍐崇瓥銆?- Decision owner: 浠撳簱缁存姢鑰?- Accepted by / date: 鏈壒鍑?- Depends on: [ADR-0001](../engineering/0001-delivery-and-durable-design.md)
- Related: [鍖呰竟鐣宂(../../architecture/package-boundaries.md)銆乕Constitution](../../../.specify/memory/constitution.md)銆乣specs/007-llm-protocol-abstraction/`锛堜粎鏈湴锛?- Supersedes: 鏃?- Superseded by: 鏃?
## Context and drivers

`packages/core/llm-provider` 涓?`packages/infra/llm-provider-langchain` 鐩墠鍙湁鍛藉悕绌洪棿楠ㄦ灦锛?灏氭棤璇锋眰銆佸搷搴斻€丳rovider 鎴栭€傞厤瀹炵幇銆傞」鐩渶瑕佹敮鎸佷笁绫诲父瑙?LLM 璋冪敤鍗忚锛?
- OpenAI Chat Completions锛?- OpenAI Responses锛?- Anthropic Messages銆?
杩欎笁绫诲崗璁殑璇锋眰鍙傛暟銆佸搷搴斿唴瀹瑰潡銆侀敊璇拰鐘舵€佽涔夊苟涓嶇瓑浠枫€傚挨鍏舵槸鈥滄€濊€冣€濆拰鈥滀笂涓嬫枃鈥濓細

- 鎺ㄧ悊寮€鍏炽€佸己搴︽。浣嶅拰 token 棰勭畻鐨勫悕绉颁笌绾︽潫涓嶅悓锛?- 鎺ㄧ悊鍐呭鍙兘甯︾鍚嶆垨涓嶉€忔槑鐘舵€侊紝澶氳疆宸ュ叿璋冪敤闇€瑕佸師鏍峰洖浼狅紱
- 鏈嶅姟绔細璇濄€佷笂涓嬫枃鍘嬬缉銆佹埅鏂拰鎻愮ず缂撳瓨灞炰簬鍗忚鐗规湁琛屼负锛?- 妯″瀷鍒楄〃閫氬父涓嶈兘璇佹槑妯″瀷鑳藉姏锛岃兘鍔涗篃涓嶅簲鍙敱妯″瀷鍚嶇О鎺ㄦ柇銆?
鍥犳锛屾妸鎵€鏈夐珮绾у弬鏁板綊涓€鍖栦负涓€涓法鍗忚鈥滈€氱敤閫夐」鈥濅細浜х敓鏈夋崯鏄犲皠锛屽苟闅愯棌鑳藉姏宸紓銆?鍙︿竴鏂归潰锛屽鏋滀笁涓崗璁畬鍏ㄧ嫭绔嬶紝涓氬姟璋冪敤鍙堜細鍦ㄥ父瑙佽矾寰勪笂閲嶅鍒嗘敮銆?
鐜版湁鍖呰竟鐣岃姹傦細`spawn-join-llm-provider` 鍙壙杞戒笌妗嗘灦鏃犲叧鐨勫崗璁拰棰嗗煙鎶借薄锛屼笉渚濊禆
LangChain 鎴栧叿浣?Provider SDK锛汱angChain 閫傞厤鍜屽叿浣撳疄鐜板睘浜?`spawn-join-llm-provider-langchain`銆傜綉缁溿€佽璇佸拰瀹㈡埛绔敓鍛藉懆鏈熷繀椤绘湁鏄庣‘鎷ユ湁鑰呫€?
鏈喅绛栦笉娑夊強鏁版嵁搴撱€佸瘑閽ュ瓨鍌ㄦ垨鐪熷疄鏈嶅姟闆嗘垚锛涜繖浜涘湪瀹炵幇闃舵鍙﹁璁捐銆?
## Options considered

1. **缁熶竴璺ㄥ崗璁姹傚拰鎺ㄧ悊/涓婁笅鏂囪涔?*锛氳皟鐢ㄦ柟鍙啓涓€濂楅珮绾у弬鏁帮紝鐢遍€傞厤鍣ㄦ槧灏勫埌涓変釜鍗忚銆?   浼樼偣鏄垏鎹㈠崗璁椂涓氬姟浠ｇ爜鍙樺寲灏忥紱缂虹偣鏄帹鐞嗘。浣嶃€侀绠椼€侀噰鏍风害鏉熴€佹湇鍔＄浼氳瘽鍜屼笂涓嬫枃
   鍘嬬缉鏃犳硶鏃犳崯绛変环锛屽鏄撻潤榛橀檷绾ф垨浜х敓閿欒璁¤垂锛屽洜姝や笉閲囩敤銆?2. **涓変釜瀹屽叏鐙珛鐨?Provider API**锛氭瘡涓崗璁嫢鏈夌嫭绔嬬殑璇锋眰銆佸搷搴斿拰璋冪敤鎺ュ彛銆備紭鐐规槸鍗忚
   宸紓鏈€娓呮锛涚己鐐规槸鏂囨湰瀵硅瘽銆佸伐鍏疯皟鐢ㄣ€佹祦寮忓拰閿欒澶勭悊绛夊叡鍚岃皟鐢ㄩ潰閲嶅锛岃皟鐢ㄦ柟鍦ㄥ父瑙?   璺緞涔熻鍒嗘敮锛屽洜姝や笉閲囩敤銆?3. **钖勫叕鍏辫皟鐢ㄥ绾?+ 鍗忚鍘熺敓绫诲瀷鍖栭€夐」 + 鐙珛娓犻亾鑳藉姏**锛氬叕鍏卞眰鍙壙璇虹湡姝ｅ彲绉绘鐨?   璇锋眰瀛楁鍜屽搷搴斿澹筹紱楂樼骇鍙傛暟浣跨敤鍗忚鍘熺敓绫诲瀷锛涙笭閬撳眰鐙珛鎵挎媴杩炴帴妫€鏌ュ拰妯″瀷鐩綍銆?   璇ユ柟妗堜繚鐣欏叡鍚岃皟鐢ㄩ潰锛屽悓鏃朵笉鍒堕€犳湁鎹熻涔夛紝閲囩敤姝ゆ柟妗堛€?
## Decision

- `spawn-join-llm-provider` 鎷ユ湁涓庢鏋舵棤鍏崇殑鍏叡娑堟伅銆佽姹傘€佸搷搴斻€佹祦寮忎簨浠躲€佽兘鍔涘０鏄庛€?  娓犻亾濂戠害鍜岀ǔ瀹氶敊璇涔夛紱涓嶅緱渚濊禆 LangChain銆丠TTP 瀹㈡埛绔垨鍏蜂綋 Provider SDK銆?- 鍏叡璇锋眰鍙寘鍚彲绉绘瀛楁锛氭秷鎭€佸伐鍏枫€佸伐鍏烽€夋嫨銆佹渶澶ц緭鍑恒€乣temperature` 鍜?`top_p`銆?  `stop`銆佹帹鐞嗐€佷笂涓嬫枃绠＄悊銆佹湇鍔＄浼氳瘽鍜岀紦瀛樼瓑鍙傛暟鏀惧叆鍗忚鍘熺敓閫夐」銆?- 涓変釜鍗忚鍚勮嚜鎷ユ湁绫诲瀷鍖栭€夐」锛?  - Chat Completions 閫夐」锛?  - Responses 閫夐」锛?  - Anthropic Messages 閫夐」銆?- 绂佹浣跨敤鏃犻檺鍒?`**kwargs`銆佷换鎰忓瓧鍏告垨瀛楃涓插寲 JSON 浣滀负鍏叡楂樼骇鍙傛暟閫氶亾銆侾rovider
  鏀跺埌涓嶅尮閰嶇殑閫夐」绫诲瀷鏃跺繀椤绘嫆缁濓紝涓嶇寽娴嬭浆鎹€?- 涓嶅缓绔嬬粺涓€鐨?`ReasoningIntent` 鎴栫粺涓€涓婁笅鏂囩瓥鐣ャ€傚崗璁棤娉曡〃杈炬垨涓嶆敮鎸佹煇涓弬鏁版椂锛?  杩斿洖鏄庣‘鐨勨€滀笉鏀寔鈥濋敊璇紱涓嶅緱闈欓粯涓㈠純銆佽繎浼兼槧灏勩€佽嚜鍔ㄩ檷绾ф垨鑷姩閲嶈瘯銆?- 鍏叡鍝嶅簲淇濈暀缁熶竴澶栧３锛屼絾鎺ㄧ悊鍐呭鍧楀繀椤绘惡甯﹀崗璁師鐢熶笉閫忔槑鐘舵€侊紝浠ユ敮鎸佸杞洖浼狅紱
  涓嶅緱鎶婃帹鐞嗗潡鍘嬫垚绾枃鏈€傛帹鐞嗗唴瀹归粯璁や笉鍐欐棩蹇椼€?- Provider 涓嶅緱鎿呰嚜瑁佸壀鍘嗗彶娑堟伅浠ラ€傞厤涓婁笅鏂囩獥鍙ｏ紱瓒呴檺杩斿洖绋冲畾閿欒锛岀敱搴旂敤鍐冲畾鎴柇銆?  鎽樿鎴栨洿鎹㈡ā鍨嬨€?- 鏈嶅姟绔細璇濄€乣store`銆乣previous_response_id` 绛夌姸鎬佸弬鏁板繀椤绘樉寮忓紑鍚紝榛樿鍏抽棴锛涘叾鏁版嵁
  鐣欏瓨鍜屽畨鍏ㄥ奖鍝嶅湪瀹炵幇闃舵鍗曠嫭璇勫銆?- 鍗忚绫诲瀷鐢辨笭閬撻厤缃樉寮忛€夋嫨锛涗笉寰楁牴鎹ā鍨嬪悕绉版帹鏂崗璁紝涔熶笉寰楀湪璇锋眰澶辫触鍚庤嚜鍔ㄥ垏鎹?  鍗忚銆?- 娓犻亾锛圕hannel锛変笌鎺ㄧ悊 Provider 鍒嗙锛氭笭閬撴嫢鏈?`ping()` 鍜?`list_models()` 绛夎繛鎺?鐩綍
  鑳藉姏锛涙帹鐞?Provider 鍙礋璐ｈ姹傚弬鏁板皝瑁呫€佽皟鐢ㄥ拰鍝嶅簲杞崲銆傚叿浣?HTTP/璁よ瘉瀹炵幇涓嶅湪鏈喅绛?  鐨勫綋鍓嶅疄鐜拌寖鍥达紝鍚庣画浠ョ嫭绔?Feature 鍜岀嫭绔?infra Distribution 璇勪及銆?- 棣栦釜 Chat Completions 瀹炵幇鏀寔 OpenAI-compatible endpoint锛汚zure OpenAI 鐨?`api-key`
  璁よ瘉銆乣api_version`銆乨eployment 鍜?URL 璇箟涓庢櫘閫?Chat Completions 涓嶅悓锛屼綔涓哄悗缁换鍔?  鍗曠嫭璁捐锛屼笉鐢?`base_url` 浼鎴愬悓涓€閰嶇疆銆?- 娓犻亾閰嶇疆鍙繚瀛樺嚟鎹紩鐢紝涓嶄繚瀛樻槑鏂囧瘑閽ワ紱鏃ュ織銆佸紓甯稿拰閰嶇疆灞曠ず涓嶅緱鍖呭惈瀵嗛挜銆佹彁绀鸿瘝銆?  鍥炵瓟姝ｆ枃鎴栨帹鐞嗗唴瀹广€?- `spawn-join-llm-provider-langchain` 鎷ユ湁涓変釜鍗忚閫傞厤鍣ㄣ€佸弬鏁版牎楠屻€丩angChain 绫诲瀷杞崲銆?  宸ュ巶鍜岃皟鐢ㄦ棩蹇楋紱LangChain 绫诲瀷涓嶅緱娉勬紡鍥炲崗璁寘銆?- 鍏叡 API 閫氳繃 `__init__.py` 鏄惧紡瀵煎嚭锛涗緷璧栨柟鍚戜繚鎸?  `llm-provider-langchain -> llm-provider -> spawn-join-core`銆?
## Key design and diagrams

鐩爣杈圭晫濡備笅锛岀澶磋〃绀轰緷璧栨垨璋冪敤鏂瑰悜锛屼笉鏄暟鎹祦鍥撅細

```text
涓氬姟搴旂敤
  鈹斺攢鈹€ LLMProvider锛堝叕鍏辨帹鐞嗗澹筹級
        鈹溾攢鈹€ ChatCompletionsProvider  -> LangChain ChatOpenAI(use_responses_api=False)
        鈹溾攢鈹€ ResponsesProvider        -> LangChain ChatOpenAI(use_responses_api=True)
        鈹斺攢鈹€ AnthropicMessagesProvider -> LangChain ChatAnthropic

娓犻亾 Channel锛堢嫭绔嬪绾︼級
  鈹溾攢鈹€ ping()
  鈹斺攢鈹€ list_models()
```

鍏抽敭涓嶅彉閲忥細

1. 鍏叡璋冪敤澶栧３涓嶅寘鍚崗璁垎鏀紱鍗忚宸紓鐢辩被鍨嬪寲閫夐」鍜岄€傞厤鍣ㄦ壙鎷呫€?2. 楂樼骇鍙傛暟鈥滀笉鏀寔鍗冲け璐モ€濓紝涓嶈繘琛屾湁鎹熻浆鎹€?3. 鎺ㄧ悊鍧楀拰宸ュ叿璋冪敤鍦ㄥ杞氦浜掍腑鍙師鏍峰洖浼犮€?4. 娓犻亾妫€鏌ヤ笉浼氶殣寮忔墽琛岀敓鎴愯姹傘€?5. 浠讳綍鏃ュ織閮戒笉鍖呭惈瀵嗛挜銆佹彁绀鸿瘝銆佸洖绛旀鏂囨垨鎺ㄧ悊鍐呭銆?
## Consequences and migration

鏀剁泭锛氳皟鐢ㄦ柟鍦ㄦ渶甯歌鐨勬枃鏈€佸伐鍏峰拰娴佸紡鍦烘櫙鍙緷璧栦竴濂楀澹筹紱鍗忚宸紓淇濇寔鏄惧紡锛涙祴璇曞彲浠?浣跨敤 fake 妯″瀷楠岃瘉濂戠害锛屼笉渚濊禆鐪熷疄鍑嵁锛涙笭閬撹兘鍔涗笌鎺ㄧ悊鑳藉姏涓嶄細浜掔浉姹℃煋銆?
鎴愭湰锛氬垏鎹㈠崗璁椂锛屼娇鐢ㄤ簡楂樼骇鍙傛暟鐨勮皟鐢ㄦ柟蹇呴』璋冩暣閫夐」鏋勯€狅紱涓変釜閫傞厤鍣ㄩ渶瑕佸垎鍒淮鎶ゅ弬鏁?鏍￠獙鍜屾槧灏勬祴璇曪紱鍗忚鐗堟湰鍙樺寲鍙兘瑕佹眰鏇存柊閫傞厤閫昏緫銆?
鍏煎鎬э細褰撳墠涓や釜鍖呭皻鏈彂甯冨叿浣撳绾︼紝鍥犳娌℃湁鏃㈡湁璋冪敤鏂归渶瑕佽縼绉汇€傛柊澧炶繍琛屾椂渚濊禆
锛堝鍏蜂綋 LangChain 闆嗘垚鍖咃級浼氬湪瀹炵幇璁″垝涓崟鐙垪鍑哄苟楠岃瘉渚濊禆鏂瑰悜銆?
閲嶆柊璇勪及瑙﹀彂鏉′欢锛?
- 涓氬姟纭疄闇€瑕佸湪杩愯鏃惰法鍗忚鍒囨崲锛屼笖鎰挎剰鎺ュ彈鏄庣‘鐨勬湁鎹熸槧灏勮鍒欙紱
- 闇€瑕佹妸娓犻亾瀹炵幇涓庝笘鐣屾ā鍨嬬洰褰曚綔涓虹嫭绔?Distribution 鍙戝竷锛?- LangChain 鎴栦笂娓稿崗璁彂鐢熺牬鍧忔€у彉鏇达紱
- 闇€瑕佹寔涔呭寲娓犻亾閰嶇疆鎴栧紩鍏ュ瘑閽ョ鐞嗘湇鍔°€?
## Verification and implementation status

瀹炵幇宸茶惤鍦板湪 `spawn-join-llm-provider` 鍜?`spawn-join-llm-provider-langchain`锛屼絾 ADR 浠嶄负
`Proposed`锛岀瓑寰呯淮鎶よ€?code review 鍜?reviewed HEAD 纭銆?
宸插疄闄呮墽琛岋細

```text
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
  缁撴灉锛歟xit 0锛?1 tests passed锛汸yright strict 0 errors锛沚uild/isolated install passed

pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
  缁撴灉锛歟xit 0锛?6 tests passed锛汸yright strict 0 errors锛沚uild/isolated install passed

pwsh -NoProfile -File scripts/quality.ps1 -Check static
  缁撴灉锛? failing check(s)

pwsh -NoProfile -File scripts/quality.ps1 -Check docs
  缁撴灉锛歟xit 0

pwsh -NoProfile -File scripts/quality.ps1 -Check governance
  缁撴灉锛? error / 0 warning
```

鏈墽琛岋細鐪熷疄妯″瀷/娓犻亾璇锋眰銆佺湡瀹炲嚟鎹泦鎴愭祴璇曘€丳ython 3.11/3.14 鏈満鐭╅樀銆傞粯璁ゆ祴璇曚娇鐢?LangChain fake 妯″瀷锛屼笉璁块棶缃戠粶銆?
宸茬煡闄愬埗锛氶儴鍒嗗ぇ鍨嬫槧灏?鏍￠獙鍑芥暟浣跨敤 `# noqa: C901` 淇濈暀绾挎€у崗璁垎鏀紝鍚庣画鍙媶鍒嗭紱娓犻亾
鐪熷疄 HTTP 鍜?Azure 涓撶敤璁よ瘉灏氭湭瀹炵幇銆?
## Revision history

- 2026-10-29锛氭彁鍑哄崗璁師鐢熼€夐」銆佹笭閬?Provider 鍒嗙涓庢帹鐞嗗潡鍥炰紶鐨勫€欓€夊喅绛栥€?- 2026-10-29锛氬疄鐜颁笁涓崗璁?Provider銆佸叕鍏卞绾﹀拰绂荤嚎娴嬭瘯锛汚DR 淇濇寔 Proposed锛岀瓑寰呬唬鐮佽瘎瀹°€?
