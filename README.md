# flask-ansible-demo
使用flask调用ansible 并且实时显示日志的demo
运行流：

```mermaid
graph TD;
  A-->B;
  A-->C;
  B-->D;
  C-->D;
  ```

最近在研究ansible，写了个简单的例子



![Alt text](/image/2.png)

``` python

  play = ExecPlaybook(['/home/sh01318/git/demo/ansible_plugins/test.yaml'], id)
  play.add_host('192.168.3.210')
  play.add_host(host='172.16.8.248', port=22, user='root', passwd='dskskdjf', private_file=None)
  play.add_playbook_vars('name', 'ceshi1')
  play.add_playbook_vars('name2', 'ceshi2')
  play.run()

```


 wechat：18516696557
