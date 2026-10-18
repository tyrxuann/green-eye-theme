import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * 测试运行器颜色样例：
 *  - passes 绿色；
 *  - intentionallyFails 红色（故意失败）；
 *  - disabled 灰色。
 */
class DebugCheckTest {

    @Test
    void passes() {
        assertEquals(3, DebugCheck.combine(1, 2));
    }

    @Test
    void intentionallyFails() {
        assertEquals(4, DebugCheck.combine(1, 2),
                "故意失败：用于查看测试失败颜色");
    }

    @Test
    @Disabled("演示禁用测试的灰色")
    void disabled() {
    }
}
