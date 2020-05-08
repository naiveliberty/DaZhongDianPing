# 大众点评信息爬取

### 声明：博客内容不得用于商业用途，仅做学习交流，如果侵犯了您的利益和权益,请邮箱联系我，我将删除该项目。

`woff2tff.py` 该文件来自于https://github.com/hanikesn/woff2otf

------

### 版本更新：

#### 2020-5-8

- 商户评论详情页面如果没有携带 cookies 访问，response 源码中电话号码后两位为 **；
- 商户评论详情页用户评论区域 svg 文件结构发生变化，新增了匹配规则;
- 美食分类页面（`http://www.dianping.com/shenzhen/ch10/g117`）,为携带 cookies 访问，返回的 html 源码为空;
- ~~dzdp_css_map_V1.0.py~~已失效，新增 `dzdp_css_map_V1.1.py`;
- 使用前请自行添加 Cookies。



| 作者    | 邮箱                 |
| ------- | -------------------- |
| liberty | fthemuse@foxmail.com |



## 环境依赖

```
pip3 install -r requirements.txt
```



## 分析过程

详见：`https://blog.csdn.net/saberqqq/article/details/105977645`