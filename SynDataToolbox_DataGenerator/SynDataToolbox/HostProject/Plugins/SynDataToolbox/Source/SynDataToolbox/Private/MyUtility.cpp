// MyUtility.cpp
#include "MyUtility.h"
#include "DrawDebugHelpers.h"
#include "Engine/World.h"

void UMyUtility::DrawSinusoidalCircle(UObject* WorldContextObject, FVector Center, float Radius, float Hieght, int32 NumberOfPoints)
{
    if (!WorldContextObject) return;
    UWorld* World = WorldContextObject->GetWorld();
    if (!World) return;

    const float AngleIncrement = 2 * PI / NumberOfPoints;
    FVector PreviousPoint = Center + FVector(Radius, 0, 0);

    for (int32 i = 1; i <= NumberOfPoints; ++i)
    {
        float Angle = i * AngleIncrement;
        FVector NextPoint = Center + FVector(Radius * FMath::Cos(Angle), Radius * FMath::Sin(Angle), FMath::Sin(2 * PI * i/10) * Hieght);

        DrawDebugLine(World, PreviousPoint, NextPoint, FColor::Green, false, -1, 0, 2.0f);
        PreviousPoint = NextPoint;
    }
}
