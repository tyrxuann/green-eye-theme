/**
 * 故意编译错误，放在 Maven 源码目录之外，避免阻塞测试。
 * 用 IntelliJ 打开本文件查看红色波浪线。
 */
public class BrokenSnippet {

    public static void main(String[] args) {
        int broken = "not an int"; // 红色波浪线
        System.out.println(broken);
    }
}
