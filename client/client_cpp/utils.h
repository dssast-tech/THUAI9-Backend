#pragma once
#include <vector>
#include <cmath>

struct Point
{
    int x, y;
    Point(int x = 0, int y = 0) : x(x), y(y) {}
};

struct DicePair
{
    int value1, value2;
};

struct Spell
{
    // 法术属性
};

struct SpellContext
{
    // 法术上下文
};

struct AttackContext
{
    // 攻击上下文
};