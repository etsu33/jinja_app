import React from "react";
import { View, Text } from "react-native";
import { spacing } from "../../app/design/spacing";

export const Spacer = ({ h = spacing.lgGap }: { h?: number }) => <View style={{ height: h }} />;

export const Section = ({
  title,
  children,
  top = spacing.lgGap,
  bottom = spacing.lgGap,
}: { title?: string; children: React.ReactNode; top?: number; bottom?: number }) => (
  <View style={{ paddingHorizontal: spacing.screenX, paddingTop: top, paddingBottom: bottom }}>
    {title ? <Text style={{ fontSize: 18, fontWeight: "700", marginBottom: spacing.smGap }}>{title}</Text> : null}
    {children}
  </View>
);
