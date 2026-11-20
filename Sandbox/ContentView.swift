import SwiftUI

struct ContentView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.42, green: 0.60, blue: 0.68),
                    Color(red: 0.86, green: 0.80, blue: 0.64),
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 12) {
                Text("Vétheuil")
                    .font(.system(size: 44, weight: .semibold, design: .serif))
                Text("Built without a Mac")
                    .font(.headline)
                    .foregroundStyle(.secondary)

                VStack(alignment: .leading, spacing: 6) {
                    row("commit", BuildInfo.commit)
                    row("built", BuildInfo.date)
                    row("toolchain", BuildInfo.toolchain)
                }
                .font(.system(.footnote, design: .monospaced))
                .padding()
                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
            }
            .padding(24)
        }
    }

    private func row(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label).foregroundStyle(.secondary)
            Spacer()
            Text(value)
        }
    }
}

#Preview {
    ContentView()
}
